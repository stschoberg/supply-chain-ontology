"""Load the ontology, scenarios, and shapes, and run reasoning, from one place.

Tests, pipelines, and the CLI all go through these helpers so they see the same graph.
"""

from __future__ import annotations

import csv
from pathlib import Path

import owlrl
from pyshacl import validate as shacl_validate
from rdflib import Graph
from rdflib.query import Result

ROOT = Path(__file__).resolve().parents[2]
ONTOLOGY_DIR = ROOT / "ontology"
EDIT_FILE = ONTOLOGY_DIR / "src" / "sco-edit.ttl"
IMPORTS_DIR = ONTOLOGY_DIR / "imports"
COMPONENTS_DIR = ONTOLOGY_DIR / "components"
CQ_DIR = ROOT / "competency-questions"
SCENARIOS_DIR = ROOT / "scenarios"
SHAPES_DIR = ROOT / "shapes"


def load_tbox() -> Graph:
    """The SCO editors' file merged with its components and imports (no network access).

    Components are generated from ROBOT templates (`make components`) and committed, so
    Python tooling works without Java.
    """
    g = Graph()
    g.parse(EDIT_FILE)
    for imp in sorted([*COMPONENTS_DIR.glob("*.owl"), *IMPORTS_DIR.glob("*.owl")]):
        g.parse(imp)
    return g


def load_shapes() -> Graph:
    g = Graph()
    for f in sorted(SHAPES_DIR.glob("*.ttl")):
        g.parse(f)
    return g


def scenario_names() -> list[str]:
    if not SCENARIOS_DIR.exists():
        return []
    return sorted(p.name for p in SCENARIOS_DIR.iterdir() if (p / "data.ttl").exists())


def load_scenario(name: str) -> Graph:
    g = Graph()
    for f in sorted((SCENARIOS_DIR / name).glob("*.ttl")):
        g.parse(f)
    return g


def reason(g: Graph) -> Graph:
    """Materialize OWL 2 RL entailments in place and return the graph.

    OWL 2 RL is a fast, pure-Python approximation good enough for instance-level CQ tests.
    Full OWL 2 DL classification and consistency checking of the TBox run with ROBOT/HermiT
    via `make reason`.
    """
    owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(g)
    return g


def reasoned_scenario(name: str) -> Graph:
    return reason(load_tbox() + load_scenario(name))


def cq_ids() -> list[str]:
    return sorted(p.stem for p in CQ_DIR.glob("CQ-*.rq"))


def run_cq(g: Graph, cq_id: str) -> Result:
    return g.query((CQ_DIR / f"{cq_id}.rq").read_text())


def rows(result: Result) -> list[tuple[str, ...]]:
    """Query results as sorted tuples of plain strings, for comparison with expected CSVs."""
    return sorted(tuple("" if v is None else str(v) for v in row) for row in result)


def expected_rows(scenario: str, cq_id: str) -> tuple[list[str], list[tuple[str, ...]]] | None:
    path = SCENARIOS_DIR / scenario / "expected" / f"{cq_id}.csv"
    if not path.exists():
        return None
    with path.open(newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        return header, sorted(tuple(r) for r in reader)


def validate(data: Graph) -> tuple[bool, str]:
    """SHACL-validate data against shapes/, using the TBox for class hierarchy lookups."""
    conforms, _, text = shacl_validate(
        data, shacl_graph=load_shapes(), ont_graph=load_tbox(), inference="rdfs"
    )
    return conforms, text
