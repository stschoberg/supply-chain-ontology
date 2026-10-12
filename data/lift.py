"""Lift a data release's tables into RDF, in each source's own terms.

Usage:
  uv run python -m data.lift [--tables data/dist] [--out data/graph]   # make lift

This is layer 1 of ADR-0005: one graph per source, `<source>.nt.gz`, written by running the YARRRML
mappings in data/mappings/<source>/ over the release's CSV files with Morph-KGC. A release build
(`data.release`) calls `lift` on its own tables. Run from the command line, it re-lifts any
directory holding a release's files: data/dist/ after `make dist`, or a downloaded release.

Morph-KGC runs as a pinned tool in its own environment (`uv run --no-project`), as ROBOT does:
its dependency pins conflict with this project's.

Output is sorted N-Triples, gzipped without a timestamp, so the same tables always give the same
bytes.
"""

import argparse
import csv
import gzip
import subprocess
import tempfile
from pathlib import Path

from rdflib import RDF

from sco import graph
from sco.namespaces import USAS

MORPH_KGC = "morph-kgc==2.10.0"
MAPPINGS_DIR = graph.ROOT / "data" / "mappings"
TABLES_DIR = graph.ROOT / "data" / "dist"
GRAPH_DIR = graph.ROOT / "data" / "graph"
# Per source: each mapped table and the class its rows are lifted to. There is one mapping file per
# table, named after it.
ROW_CLASSES = {"usaspending": {"stg_usaspending__awards": USAS.Award, "entities": USAS.Entity}}


def run_mappings(mappings: list[Path], tables: Path) -> list[str]:
    """Run Morph-KGC from `tables`, where the mappings' sources are, and return sorted triples."""
    with tempfile.TemporaryDirectory() as tmp:
        config, output = Path(tmp) / "config.ini", Path(tmp) / "graph.nt"
        config.write_text(
            f"[CONFIGURATION]\noutput_file: {output}\nlogging_level: WARNING\n"
            f"[DataSource]\nmappings: {','.join(str(m) for m in mappings)}\n"
        )
        subprocess.run(
            ["uv", "run", "--no-project", "--python", "3.12", "--with", MORPH_KGC,
             "python", "-m", "morph_kgc", str(config)],
            cwd=tables,
            check=True,
        )  # fmt: skip
        return sorted(set(output.read_text().splitlines()))


def check_rows(table: str, row_class: str, triples: list[str], tables: Path) -> None:
    """Every row became a node, and no node was made that isn't a row (a dangling foreign key)."""
    with (tables / f"{table}.csv").open(newline="") as fh:
        rows = sum(1 for _ in csv.reader(fh)) - 1
    typed = f"<{RDF.type}> <{row_class}> ."
    lifted = sum(1 for t in triples if t.endswith(typed))
    if lifted != rows:
        raise SystemExit(f"error: {table} has {rows:,} rows but {lifted:,} were lifted")


def lift(source: str, tables: Path, out: Path) -> Path:
    row_classes = ROW_CLASSES[source]
    triples = run_mappings([MAPPINGS_DIR / source / f"{t}.yml" for t in row_classes], tables)
    for table, row_class in row_classes.items():
        check_rows(table, row_class, triples, tables)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{source}.nt.gz"
    # No file name or mtime in the gzip header: the same triples always produce the same file.
    with path.open("wb") as fh, gzip.GzipFile(filename="", fileobj=fh, mode="wb", mtime=0) as gz:
        gz.write(("\n".join(triples) + "\n").encode())
    print(f"  {path.name:32} {len(triples):>9,} triples {path.stat().st_size / 1e6:8.2f} MB")
    return path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tables", default=str(TABLES_DIR), help="directory of a release's files")
    parser.add_argument("--out", default=str(GRAPH_DIR))
    args = parser.parse_args(argv)
    tables = Path(args.tables).resolve()
    if not any(tables.glob("*.csv")):
        raise SystemExit(f"error: no tables in {tables}; run 'make dist' or download a release")
    for source in sorted(ROW_CLASSES):
        lift(source, tables, Path(args.out).resolve())


if __name__ == "__main__":
    main()
