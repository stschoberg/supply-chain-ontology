"""Lift a data release's tables into RDF graphs: one per source, then one per model.

Usage:
  uv run python -m data.lift [--tables data/dist] [--out data/graph]   # make lift
  uv run python -m data.lift --examples                                # make lift-examples
  uv run python -m data.lift --schemas                                 # make lift-schemas

The two layers of ADR-0005. Each graph is written as a pair:

  <name>.schema.ttl   its classes and properties, with no instance data
  <name>.nt.gz        the schema plus all the instance data: the one file to load and query

1. Source graphs, one per source: the tables in the source's own terms, written by running the
   YARRRML mappings in data/mappings/<source>/ (`<table>.yml`) over the release's CSV files with
   Morph-KGC. The schema is that directory's `schema.ttl`.
2. Model graphs, one per model in MODELS: every source's graph mapped into that model's terms by
   the SPARQL CONSTRUCT rules in data/mappings/<source>/<model>/. The schema is the model's own
   ontology. A model graph says things about the same nodes as the source graphs, so the two can
   be loaded together. An experimental model's graph is named `<model>.experimental.nt.gz`.

A release build (`data.release`) does all of this on its own tables and ships the results.

`--tables` is any directory holding a release's files: data/dist/ after `make dist`, or a downloaded
release. `--examples` instead rebuilds each mapping's committed `example/lifted.ttl` from its
`example/source.nt`. `--schemas` rebuilds data/schemas/, after a model's ontology changes.

Morph-KGC runs as a pinned tool in its own environment (`uv run --no-project`), as ROBOT does:
its dependency pins conflict with this project's.

Output is sorted N-Triples, gzipped without a timestamp, so the same tables always give the same
bytes.
"""

import argparse
import csv
import gzip
import shutil
import subprocess
import tempfile
from pathlib import Path

from rdflib import OWL, RDF, RDFS, Graph, Literal, Namespace
from rdflib.compare import to_canonical_graph

from sco import fetching, graph
from sco.namespaces import DATA, PREFIXES, USAS

MORPH_KGC = "morph-kgc==2.10.0"
MAPPINGS_DIR = graph.ROOT / "data" / "mappings"
SCHEMAS_DIR = graph.ROOT / "data" / "schemas"
TABLES_DIR = graph.ROOT / "data" / "dist"
GRAPH_DIR = graph.ROOT / "data" / "graph"
PROV = Namespace("http://www.w3.org/ns/prov#")
# Per source: each mapped table and the class its rows are lifted to. There is one mapping file per
# table, named after it.
ROW_CLASSES = {"usaspending": {"stg_usaspending__awards": USAS.Award, "entities": USAS.Entity}}
SOURCE_LABELS = {"usaspending": "USAspending.gov contract awards, in the source's own terms"}
# The models sources are mapped into. `schema` is the model's ontology as one file. An experimental
# model's rules are incomplete and will change; its graph says so in its file name, so nobody
# mistakes one in a release for settled data.
MODELS = {
    "iof-scro": {
        "label": "Awards in the terms of IOF Core and the IOF Supply Chain Reference Ontology",
        "schema": graph.ROOT / "research" / "reference" / "iof-scro" / "build" / "iof-reasoned.ttl",
        "experimental": True,
    },
}


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


def write_triples(path: Path, triples: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # No file name or mtime in the gzip header: the same triples always produce the same file.
    with path.open("wb") as fh, gzip.GzipFile(filename="", fileobj=fh, mode="wb", mtime=0) as gz:
        gz.write(("\n".join(triples) + "\n").encode())
    print(f"  {path.name:32} {len(triples):>9,} triples {path.stat().st_size / 1e6:8.2f} MB")
    return path


def graph_iri(name: str) -> str:
    """A graph's own name, as an N-Triples term."""
    return f"<{DATA}graph/{name}>"


def hydrate(name: str, label: str, version: str, schema: list[str], instances: list[str],
            derived_from: list[str]) -> list[str]:  # fmt: skip
    """A graph's schema and instance triples under one header naming the graph and its release.

    The schema's own ontology header is replaced by the graph's, which points back to it, so OWL
    tools find a single ontology in the file.
    """
    typed = f" <{RDF.type}> <{OWL.Ontology}> ."
    ontologies = [line.removesuffix(typed) for line in schema if line.endswith(typed)]
    schema = [line for line in schema if not line.startswith(tuple(f"{o} " for o in ontologies))]
    iri = graph_iri(name)
    header = [
        f"{iri} <{RDF.type}> <{OWL.Ontology}> .",
        f"{iri} <{RDFS.label}> {Literal(label, lang='en').n3()} .",
        f"{iri} <{OWL.versionInfo}> {Literal(version).n3()} .",
        *(f"{iri} <{PROV.wasDerivedFrom}> {origin} ." for origin in [*derived_from, *ontologies]),
    ]
    return sorted({*header, *schema, *instances})


def lift(source: str, tables: Path, out: Path, version: str = "unreleased") -> Path:
    """Layer 1: a release's tables as a graph in the source's own terms, with its schema."""
    row_classes = ROW_CLASSES[source]
    triples = run_mappings([MAPPINGS_DIR / source / f"{t}.yml" for t in row_classes], tables)
    for table, row_class in row_classes.items():
        check_rows(table, row_class, triples, tables)
    out.mkdir(parents=True, exist_ok=True)
    schema_file = MAPPINGS_DIR / source / "schema.ttl"
    shutil.copy(schema_file, out / f"{source}.schema.ttl")
    schema = Graph().parse(schema_file).serialize(format="nt").splitlines()
    hydrated = hydrate(source, SOURCE_LABELS[source], version, schema, triples, [])
    return write_triples(out / f"{source}.nt.gz", hydrated)


def schema_stamp(model: str) -> str:
    """First line of data/schemas/<model>.nt: which ontology file it was built from."""
    schema = MODELS[model]["schema"]
    return f"# sha256 of {schema.relative_to(graph.ROOT)}: {fetching.sha256(schema)}"


def build_schemas() -> None:
    """Rewrite data/schemas/<model>.nt: each model's ontology as N-Triples with stable names for
    its unnamed nodes, so graphs that include it are the same bytes every time. Naming them takes
    most of a minute, which is why the result is committed and not redone on every lift."""
    for model, config in MODELS.items():
        canonical = to_canonical_graph(Graph().parse(config["schema"]))
        triples = sorted(set(canonical.serialize(format="nt").splitlines()) - {""})
        path = SCHEMAS_DIR / f"{model}.nt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join([schema_stamp(model), *triples]) + "\n")
        print(f"  {path.relative_to(graph.ROOT)}: {len(triples):,} triples")


def model_schema(model: str) -> list[str]:
    path = SCHEMAS_DIR / f"{model}.nt"
    stamp, *triples = path.read_text().splitlines()
    if stamp != schema_stamp(model):
        raise SystemExit(
            f"error: {path.relative_to(graph.ROOT)} is out of date with the model's ontology; "
            "run 'make lift-schemas' and commit"
        )
    return triples


def rules(source: str, model: str) -> Path:
    """The SPARQL CONSTRUCT rules that map one source into one model's terms."""
    return MAPPINGS_DIR / source / model


def lift_models(source_graphs: dict[str, Path], out: Path, version: str = "unreleased") -> dict:
    """Layer 2: one graph per model, holding every source that has rules for it, with the model's
    schema. Returns {model: file}."""
    parsed, paths = {}, {}
    for model, config in MODELS.items():
        sources = [s for s in source_graphs if any(rules(s, model).glob("*.rq"))]
        if not sources:
            continue
        instances = set()
        for source in sources:
            if source not in parsed:
                data = gzip.decompress(source_graphs[source].read_bytes())
                parsed[source] = Graph().parse(data=data, format="nt")
            lifted = graph.construct(parsed[source], rules(source, model))
            instances |= set(lifted.serialize(format="nt").splitlines()) - {""}
        out.mkdir(parents=True, exist_ok=True)
        shutil.copy(config["schema"], out / f"{model}.schema.ttl")
        hydrated = hydrate(
            model, config["label"], version, model_schema(model), sorted(instances),
            [graph_iri(source) for source in sources],
        )  # fmt: skip
        name = f"{model}.experimental" if config["experimental"] else model
        paths[model] = write_triples(out / f"{name}.nt.gz", hydrated)
    return paths


def build_examples() -> None:
    """Rewrite each mapping's example/lifted.ttl from its example/source.nt."""
    for source in sorted(ROW_CLASSES):
        for model in MODELS:
            example = rules(source, model) / "example"
            if not example.exists():
                continue
            lifted = graph.construct(Graph().parse(example / "source.nt"), rules(source, model))
            for prefix, namespace in PREFIXES.items():
                lifted.bind(prefix, namespace)
            lifted.serialize(example / "lifted.ttl", format="turtle")
            print(f"  {(example / 'lifted.ttl').relative_to(graph.ROOT)}: {len(lifted):,} triples")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--tables", default=str(TABLES_DIR), help="directory of a release's files")
    parser.add_argument("--out", default=str(GRAPH_DIR))
    parser.add_argument("--examples", action="store_true", help="rebuild the committed examples")
    parser.add_argument("--schemas", action="store_true", help="rebuild data/schemas/")
    args = parser.parse_args(argv)
    if args.examples or args.schemas:
        build_examples() if args.examples else build_schemas()
        return
    tables, out = Path(args.tables).resolve(), Path(args.out).resolve()
    if not any(tables.glob("*.csv")):
        raise SystemExit(f"error: no tables in {tables}; run 'make dist' or download a release")
    lift_models({source: lift(source, tables, out) for source in sorted(ROW_CLASSES)}, out)


if __name__ == "__main__":
    main()
