"""Build a versioned data release in data/dist/.

Usage:
  uv run python -m data.release build [--tag data-YYYY-MM-DD]   # default: today's date, .2, .3, ...
  uv run python -m data.release publish        # normally run by .github/workflows/data-release.yml
  uv run python -m data.release catalog --base-url URL

A release contains:
  <model>.parquet      one file per published dbt model (tag:published); the data product. Table and
                       column descriptions ride along in the Parquet key-value metadata.
  <model>.csv          the same rows as CSV, for spreadsheets and tools without Parquet support
  catalog.duckdb       views over those Parquet files, so `attach` gives named, commented tables;
                       holds no data
  raw-<source>.tar     the raw snapshot each table was built from, for exact reproduction
  RELEASE_NOTES.md     how to connect, row counts, the data dictionary, provenance
  SHA256SUMS

dbt builds into a temporary database, so a local `data/warehouse.duckdb` session never conflicts.

DuckDB resolves a view's Parquet files when the view is created, so a catalog can only point at
files that already exist. `build` points it at the local files in data/dist/; `publish` uploads the
Parquet first, then rebuilds the catalog against the release URLs.
"""

import argparse
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import duckdb

from data import dictionary
from sco import fetching, graph

REPO = os.environ.get("GITHUB_REPOSITORY", "stschoberg/supply-chain-ontology")
LATEST_TAG = "data-latest"
COLAB_URL = f"https://colab.research.google.com/github/{REPO}/blob/main/data/examples/explore.ipynb"
DIST_DIR = graph.ROOT / "data" / "dist"
TRANSFORM_DIR = dictionary.TRANSFORM_DIR
SOURCES = {"usaspending": graph.ROOT / "data" / "sources" / "usaspending" / "raw"}


def newest_snapshot(raw_dir: Path) -> Path:
    snapshots = sorted(p for p in raw_dir.glob("20*") if p.is_dir())
    if not snapshots:
        raise SystemExit(f"error: no snapshots in {raw_dir.relative_to(graph.ROOT)}; fetch first")
    return snapshots[-1]


def git_state() -> tuple[str, bool]:
    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=graph.ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()

    return git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))


def run_dbt(warehouse: Path, target: Path, dbt_vars: dict) -> None:
    subprocess.run(
        [
            "dbt", "build", "--quiet",
            "--project-dir", str(TRANSFORM_DIR),
            "--profiles-dir", str(TRANSFORM_DIR),
            "--target-path", str(target),
            "--log-path", str(target / "logs"),
            "--vars", json.dumps(dbt_vars),
        ],
        env={**os.environ, "SCO_WAREHOUSE": str(warehouse)},
        check=True,
    )  # fmt: skip


def sql_string(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def export_tables(warehouse: Path, tables: dictionary.Tables, out: Path) -> dict[str, dict]:
    """Write each table as Parquet, with its descriptions as key-value metadata, and as CSV."""
    stats = {}
    with duckdb.connect(str(warehouse), read_only=True) as con:
        for model, table in tables.items():
            path = out / f"{model}.parquet"
            columns = {name: c["description"] for name, c in table["columns"].items()}
            metadata = (
                f"{{description: {sql_string(table['description'])}, "
                f"column_descriptions: {sql_string(json.dumps(columns))}}}"
            )
            # Sorted so the same data always produces the same files.
            con.sql(
                f"copy (select * from {model} order by all) to '{path}' "
                f"(format parquet, compression zstd, kv_metadata {metadata})"
            )
            con.sql(f"copy (from '{path}') to '{path.with_suffix('.csv')}' (header)")
            rows = con.sql(f"select count(*) from {model}").fetchone()[0]
            stats[model] = {"rows": rows, "columns": len(con.sql(f"describe {model}").fetchall())}
    return stats


def parquet_descriptions(con: duckdb.DuckDBPyConnection, path: Path) -> tuple[str, dict]:
    metadata = dict(
        con.sql(f"select decode(key), decode(value) from parquet_kv_metadata('{path}')").fetchall()
    )
    return metadata.get("description", ""), json.loads(metadata.get("column_descriptions", "{}"))


def write_catalog(out: Path, base_url: str) -> None:
    """(Re)write catalog.duckdb with a view per Parquet file in `out`, and refresh SHA256SUMS.

    Each view and column is commented with the descriptions stored in its Parquet file.
    """
    path = out / "catalog.duckdb"
    path.unlink(missing_ok=True)
    with duckdb.connect(str(path)) as con:
        for parquet in sorted(out.glob("*.parquet")):
            model = parquet.stem
            con.sql(
                f"create view {model} as select * from read_parquet('{base_url}/{model}.parquet')"
            )
            description, columns = parquet_descriptions(con, parquet)
            if description:
                con.sql(f"comment on view {model} is {sql_string(description)}")
            for column, text in columns.items():
                con.sql(f"comment on column {model}.{column} is {sql_string(text)}")
    sums = [f"{fetching.sha256(f)}  {f.name}" for f in sorted(out.iterdir()) if f.is_file()]
    (out / "SHA256SUMS").write_text(
        "\n".join(f for f in sums if not f.endswith("SHA256SUMS")) + "\n"
    )


def archive_raw(source: str, snapshot: Path, out: Path) -> str:
    """Tar the snapshot's original zips and manifests (not the extracted CSVs)."""
    name = f"raw-{source}-{snapshot.name}.tar"
    with tarfile.open(out / name, "w") as tar:
        for f in sorted(snapshot.glob("*.zip")) + sorted(snapshot.glob("*.manifest.json")):
            tar.add(f, arcname=f"{source}/{snapshot.name}/{f.name}")
    return name


def release_notes(tag: str, sha: str, dirty: bool, tables, stats, raw, sources) -> str:
    table_rows = "\n".join(f"| `{m}` | {t['rows']:,} | {t['columns']} |" for m, t in stats.items())
    source_rows = "\n".join(
        f"| {s} | {snap.name} | `{name}` |"
        for (s, snap), name in zip(sources.items(), raw, strict=True)
    )
    first = next(iter(stats), "awards")
    base_url = release_url(tag)
    built = f"{datetime.now(UTC):%Y-%m-%d %H:%M UTC} from commit `{sha[:12]}`"
    if dirty:
        built += " (with uncommitted changes)"
    return f"""# {tag}

Built {built}.

## Connect

```sql
-- DuckDB: named tables, data read from the Parquet files on demand.
-- Use the {LATEST_TAG} release instead of {tag} for whatever is newest.
attach '{base_url}/catalog.duckdb' as sco;
select * from sco.{first} limit 10;

-- Any Parquet reader (DuckDB, pandas, polars, R, Spark)
select * from read_parquet('{base_url}/{first}.parquet');
```

- **Spreadsheets:** download `{first}.csv` from this release.
- **No install:** the [example notebook]({COLAB_URL}) runs in Google Colab.

## Tables

| Table | Rows | Columns |
|---|---|---|
{table_rows}

The caveats that matter most for using this data are in the repo's
[data README](https://github.com/{REPO}/blob/{sha}/data/README.md#what-it-can-and-cant-tell-you).

## Data dictionary

{dictionary.render(tables, level=3)}
## Sources

| Source | Snapshot | Raw archive |
|---|---|---|
{source_rows}

`meta_source_files` lists every raw file with its sha256. All sources are U.S. Government works in
the public domain.
"""


def release_url(tag: str) -> str:
    return f"https://github.com/{REPO}/releases/download/{tag}"


def next_tag(date: str) -> str:
    """data-<date>, or data-<date>.2, .3, ... if earlier releases took it the same day."""
    tag, n = f"data-{date}", 1
    while release_exists(tag):
        n += 1
        tag = f"data-{date}.{n}"
    return tag


def build(args: argparse.Namespace) -> None:
    tag = args.tag or next_tag(f"{datetime.now(UTC):%Y-%m-%d}")
    overrides = dict(o.partition("=")[::2] for o in args.snapshot)
    sources = {
        name: Path(overrides[name]).resolve() if name in overrides else newest_snapshot(raw)
        for name, raw in SOURCES.items()
    }
    sha, dirty = git_state()

    out = Path(args.out)
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)

    with tempfile.TemporaryDirectory() as tmp:
        warehouse, target = Path(tmp) / "warehouse.duckdb", Path(tmp) / "target"
        dbt_vars = {f"{name}_snapshot": str(path) for name, path in sources.items()}
        dbt_vars |= {"release_tag": tag, "git_sha": sha, "git_dirty": dirty}
        print(f"Building {tag} from {', '.join(f'{s} {p.name}' for s, p in sources.items())}")
        run_dbt(warehouse, target, dbt_vars)
        tables = dictionary.published_tables(target / "manifest.json")
        stats = export_tables(warehouse, tables, out)

    raw = [archive_raw(name, snap, out) for name, snap in sources.items()]
    notes = release_notes(tag, sha, dirty, tables, stats, raw, sources)
    (out / "RELEASE_NOTES.md").write_text(notes)
    write_catalog(out, out.resolve().as_posix())

    for f in sorted(out.iterdir()):
        print(f"  {f.name:32} {f.stat().st_size / 1e6:8.2f} MB")
    print(f"Wrote {out}. Its catalog.duckdb points at these local files.")


def gh(*args: str) -> None:
    subprocess.run(["gh", *args, "--repo", REPO], check=True)


def release_exists(tag: str) -> bool:
    view = subprocess.run(
        ["gh", "release", "view", tag, "--repo", REPO], capture_output=True, text=True
    )
    if view.returncode == 0:
        return True
    if "release not found" in view.stderr:
        return False
    # Anything else (logged out, no network) must not pass for "free": a wrong answer picks a
    # tag that's already taken.
    raise SystemExit(f"error: can't check for release {tag}: {view.stderr.strip()}")


def row_counts(source: str) -> dict[str, int]:
    """Rows per table, read through a catalog (path or URL) or from local Parquet files."""
    with duckdb.connect() as con:
        if source.endswith(".duckdb"):
            con.sql(f"attach '{source}' as sco (read_only)")
            tables = [
                r[0]
                for r in con.sql(
                    "select view_name from duckdb_views() where database_name = 'sco'"
                ).fetchall()
            ]
            return {
                t: con.sql(f"select count(*) from sco.{t}").fetchone()[0] for t in sorted(tables)
            }
        files = sorted(Path(source).glob("*.parquet"))
        return {f.stem: con.sql(f"select count(*) from '{f}'").fetchone()[0] for f in files}


def verify(tag: str, expected: dict[str, int]) -> None:
    """Attach the published catalog from a fresh session and compare row counts with the build."""
    published = row_counts(f"{release_url(tag)}/catalog.duckdb")
    if published != expected:
        raise SystemExit(f"error: {tag} serves {published}, expected {expected}")
    print(f"Verified {tag}: {', '.join(f'{t} {n:,}' for t, n in published.items())}")


def publish(args: argparse.Namespace) -> None:
    out = Path(args.out)
    with duckdb.connect() as con:
        tag, sha, dirty = con.sql(
            f"select release_tag, git_sha, git_dirty from '{out / 'meta_build.parquet'}'"
        ).fetchone()
    if dirty and not args.allow_dirty:
        raise SystemExit("error: data/dist was built from uncommitted changes; commit and rebuild")
    if release_exists(tag):
        raise SystemExit(f"error: release {tag} already exists, and releases are immutable")

    expected = row_counts(str(out))
    data_files = [
        str(f) for f in sorted(out.iterdir()) if f.name not in ("catalog.duckdb", "SHA256SUMS")
    ]
    notes = out / "RELEASE_NOTES.md"

    print(f"Creating release {tag}")
    gh("release", "create", tag, *data_files, "--title", tag, "--notes-file", str(notes),
       "--target", sha, "--latest=false")  # fmt: skip
    # Only now do the Parquet URLs exist, so only now can the catalog be built against them.
    write_catalog(out, release_url(tag))
    gh("release", "upload", tag, str(out / "catalog.duckdb"), str(out / "SHA256SUMS"))
    verify(tag, expected)

    # Recreate (rather than update) the moving release, so no stale assets survive.
    print(f"Pointing {LATEST_TAG} at {tag}")
    if release_exists(LATEST_TAG):
        gh("release", "delete", LATEST_TAG, "--cleanup-tag", "--yes")
    latest_notes = out / "LATEST_NOTES.md"
    latest_notes.write_text(
        f"Moving pointer to the newest data release, currently **{tag}**. Its catalog reads the "
        f"Parquet files of {tag}. Cite the dated release in written work, not this one.\n\n"
        + notes.read_text()
    )
    files = [str(f) for f in sorted(out.iterdir()) if f.name != latest_notes.name]
    gh("release", "create", LATEST_TAG, *files, "--title", f"{LATEST_TAG} ({tag})",
       "--notes-file", str(latest_notes), "--target", sha, "--latest=false")  # fmt: skip
    latest_notes.unlink()
    print(f"Published https://github.com/{REPO}/releases/tag/{tag}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    b = commands.add_parser("build", help="build a release into data/dist/")
    b.add_argument("--tag", help="release tag (default: data-<today>, then .2, .3, ...)")
    b.add_argument("--out", default=str(DIST_DIR), help="output directory")
    b.add_argument(
        "--snapshot", action="append", default=[], metavar="SOURCE=PATH",
        help="use this snapshot instead of the newest one",
    )  # fmt: skip
    p = commands.add_parser("publish", help="publish data/dist/ as a GitHub release (CI)")
    p.add_argument("--out", default=str(DIST_DIR), help="release directory built by `build`")
    p.add_argument("--allow-dirty", action="store_true", help="publish a build of uncommitted code")
    c = commands.add_parser(
        "catalog", help="repoint catalog.duckdb at Parquet files served elsewhere"
    )
    c.add_argument("--base-url", required=True, help="URL or directory holding the Parquet files")
    c.add_argument("--out", default=str(DIST_DIR), help="release directory")
    args = parser.parse_args(argv)
    if args.command == "build":
        build(args)
    elif args.command == "publish":
        publish(args)
    else:
        write_catalog(Path(args.out), args.base_url.rstrip("/"))


if __name__ == "__main__":
    main()
