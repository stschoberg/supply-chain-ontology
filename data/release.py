"""Build a versioned data release in data/dist/.

Usage:
  uv run python -m data.release build [--tag data-YYYY-MM-DD]
  uv run python -m data.release catalog --base-url URL

A release contains:
  <model>.parquet      one file per published dbt model (tag:published); the data product
  catalog.duckdb       views over those Parquet files, so `attach` gives named tables; holds no data
  raw-<source>.tar     the raw snapshot each table was built from, for exact reproduction
  RELEASE_NOTES.md     provenance, row counts, and how to connect
  SHA256SUMS

dbt builds into a temporary database, so a local `data/warehouse.duckdb` session never conflicts.

DuckDB resolves a view's Parquet files when the view is created, so a catalog can only point at
files that already exist. `build` points it at the local files in data/dist/; publishing uploads the
Parquet first, then rebuilds the catalog against the release URLs with `catalog`.
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

from sco import fetching, graph

REPO = "stschoberg/supply-chain-ontology"
DIST_DIR = graph.ROOT / "data" / "dist"
TRANSFORM_DIR = graph.ROOT / "data" / "transform"
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


def published_models(manifest: Path) -> list[str]:
    nodes = json.loads(manifest.read_text())["nodes"].values()
    return sorted(
        n["alias"] for n in nodes if n["resource_type"] == "model" and "published" in n["tags"]
    )


def export_parquet(warehouse: Path, models: list[str], out: Path) -> dict[str, dict]:
    tables = {}
    with duckdb.connect(str(warehouse), read_only=True) as con:
        for model in models:
            path = out / f"{model}.parquet"
            # Sorted so the same data always produces the same file.
            con.sql(
                f"copy (select * from {model} order by all) to '{path}' "
                "(format parquet, compression zstd)"
            )
            rows = con.sql(f"select count(*) from {model}").fetchone()[0]
            columns = len(con.sql(f"describe {model}").fetchall())
            tables[model] = {"rows": rows, "columns": columns}
    return tables


def write_catalog(out: Path, base_url: str) -> None:
    """(Re)write catalog.duckdb with a view per Parquet file in `out`, and refresh SHA256SUMS."""
    path = out / "catalog.duckdb"
    path.unlink(missing_ok=True)
    with duckdb.connect(str(path)) as con:
        for model in sorted(p.stem for p in out.glob("*.parquet")):
            con.sql(
                f"create view {model} as select * from read_parquet('{base_url}/{model}.parquet')"
            )
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


def release_notes(tag: str, sha: str, dirty: bool, tables, raw, sources) -> str:
    table_rows = "\n".join(f"| `{m}` | {t['rows']:,} | {t['columns']} |" for m, t in tables.items())
    source_rows = "\n".join(
        f"| {s} | {snap.name} | `{name}` |"
        for (s, snap), name in zip(sources.items(), raw, strict=True)
    )
    first = next(iter(tables), "awards")
    base_url = release_url(tag)
    built = f"{datetime.now(UTC):%Y-%m-%d %H:%M UTC} from commit `{sha[:12]}`"
    if dirty:
        built += " (with uncommitted changes)"
    return f"""# {tag}

Built {built}.

## Connect

```sql
-- DuckDB: named tables, data read from the Parquet files on demand
attach '{base_url}/catalog.duckdb' as sco;
select * from sco.{first} limit 10;

-- Any Parquet reader (DuckDB, pandas, polars, R, Spark)
select * from read_parquet('{base_url}/{first}.parquet');
```

## Tables

| Table | Rows | Columns |
|---|---|---|
{table_rows}

Column definitions: `data/transform/models/` in the repo at this commit.

## Sources

| Source | Snapshot | Raw archive |
|---|---|---|
{source_rows}

`meta_source_files` lists every raw file with its sha256. All sources are U.S. Government works in
the public domain.
"""


def release_url(tag: str) -> str:
    return f"https://github.com/{REPO}/releases/download/{tag}"


def build(args: argparse.Namespace) -> None:
    tag = args.tag or f"data-{datetime.now(UTC):%Y-%m-%d}"
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
        models = published_models(target / "manifest.json")
        tables = export_parquet(warehouse, models, out)

    raw = [archive_raw(name, snap, out) for name, snap in sources.items()]
    (out / "RELEASE_NOTES.md").write_text(release_notes(tag, sha, dirty, tables, raw, sources))
    write_catalog(out, out.resolve().as_posix())

    for f in sorted(out.iterdir()):
        print(f"  {f.name:32} {f.stat().st_size / 1e6:8.2f} MB")
    print(f"Wrote {out}. Its catalog.duckdb points at these local files.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    b = commands.add_parser("build", help="build a release into data/dist/")
    b.add_argument("--tag", help="release tag (default: data-<today>)")
    b.add_argument("--out", default=str(DIST_DIR), help="output directory")
    b.add_argument(
        "--snapshot", action="append", default=[], metavar="SOURCE=PATH",
        help="use this snapshot instead of the newest one",
    )  # fmt: skip
    c = commands.add_parser(
        "catalog", help="repoint catalog.duckdb at Parquet files served elsewhere"
    )
    c.add_argument("--base-url", required=True, help="URL or directory holding the Parquet files")
    c.add_argument("--out", default=str(DIST_DIR), help="release directory")
    args = parser.parse_args(argv)
    if args.command == "build":
        build(args)
    else:
        write_catalog(Path(args.out), args.base_url.rstrip("/"))


if __name__ == "__main__":
    main()
