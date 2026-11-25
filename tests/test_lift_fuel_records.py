"""Layer 1 of the fuel records. The checks every source shares are in test_lift.py."""

import pytest
from rdflib import RDF, Graph, Literal, URIRef

from data import lift
from sco.namespaces import DATA, FUEL_RECORDS

SOURCE = "fuel_records"
DIR = lift.MAPPINGS_DIR / SOURCE
TABLES = lift.STUDY_ROW_CLASSES[SOURCE]


@pytest.fixture(scope="module")
def g():
    return Graph().parse(DIR / "source.nt")


def test_source_graph_is_up_to_date_with_the_tables_and_mappings():
    committed = (DIR / "source.nt").read_text().splitlines()
    assert lift.lift_study(SOURCE) == committed, "run `make lift-examples` and commit"


def test_every_node_is_synthetic_and_kept_apart(g):
    nodes = set(g.subjects()) | {
        o for o in g.objects() if isinstance(o, URIRef) and o.startswith(DATA)
    }
    assert all(str(n).startswith(f"{DATA}synthetic/fuel/") for n in nodes)
    assert set(g.objects(predicate=FUEL_RECORDS.synthetic)) == {Literal(True)}


def test_no_node_is_a_portion_of_fuel_or_a_batch(g):
    # The design rule: layer 1 holds only what the records hold. Every node is a row of a table, and
    # batch numbers stay literals, because no record is a batch.
    assert set(g.objects(predicate=RDF.type)) == set(TABLES.values())
    for p in (FUEL_RECORDS.batchNumber, FUEL_RECORDS.batchOrCargo, FUEL_RECORDS.sourceBatch):
        assert all(isinstance(o, Literal) for o in g.objects(predicate=p))


def test_missing_values_produce_no_triples(g):
    refinery = DATA["synthetic/fuel/activity/ZR0001"]
    assert g.value(refinery, FUEL_RECORDS.capitalized) is None
    assert not any(isinstance(o, Literal) and str(o) == "" for o in g.objects())
