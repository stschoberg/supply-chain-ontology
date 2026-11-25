"""The SCRO reading of the fuel records (ADR-0006): what IOF Core and SCRO make of them."""

import csv

import pytest
from rdflib import RDF, Graph, Literal, Namespace
from rdflib.compare import to_isomorphic

from data import lift
from sco import graph, iof_stack
from sco.namespaces import DATA, FUEL_RECORDS, IOF, OBO

READING = lift.MAPPINGS_DIR / "fuel_records" / "iof-scro"
FUEL = Namespace(DATA["synthetic/fuel/"])
CQS = sorted((READING / "cq").glob("CQ-*.rq"))


@pytest.fixture(scope="module")
def source():
    return Graph().parse(lift.MAPPINGS_DIR / "fuel_records" / "source.nt")


@pytest.fixture(scope="module")
def lifted():
    return Graph().parse(READING / "lifted.ttl")


@pytest.fixture(scope="module")
def stack():
    return Graph().parse(iof_stack.BUILD / "iof-reasoned.ttl")


@pytest.fixture(scope="module")
def reasoned(lifted, stack):
    return graph.reason(stack + lifted)


def members(g, cls):
    return {s for s in g.subjects(RDF.type, cls) if str(s).startswith(FUEL)}


def test_lifted_is_up_to_date_with_the_rules(source, lifted):
    rebuilt = graph.construct(source, READING)
    # Through Turtle and back, as the committed file was, so numbers are written the same way.
    rebuilt = Graph().parse(data=rebuilt.serialize(format="turtle"), format="turtle")
    assert to_isomorphic(rebuilt) == to_isomorphic(lifted), "run `make lift-examples` and commit"


def test_the_reading_is_never_released():
    assert "fuel_records" not in lift.ROW_CLASSES
    assert READING in lift.readings("fuel_records")
    assert all(
        READING != lift.rules(source, model) for source in lift.ROW_CLASSES for model in lift.MODELS
    )


def test_rules_use_only_terms_the_pinned_iof_release_declares(lifted, stack):
    used = {t for triple in lifted for t in triple if str(t).startswith((str(IOF), str(OBO)))}
    assert used
    assert not {t for t in used if (t, RDF.type, None) not in stack}


def test_everything_said_is_about_the_invented_records(lifted):
    assert all(str(s).startswith(FUEL) for s in lifted.subjects())


def test_no_class_scro_defines_is_asserted(lifted):
    defined = [IOF.Lot, IOF.LotIdentifier, IOF.Sublot, IOF.Shipment, IOF.TraceableResourceUnit,
               IOF.Classifier, IOF.IndustrialInventory, IOF.MaterialProduct]  # fmt: skip
    assert not any(members(lifted, cls) for cls in defined)


def test_the_reasoner_infers_shipments_but_no_lot(lifted, reasoned):
    shipments = {
        lifted.value(s, IOF.isAbout)
        for s in members(lifted, IOF.DescriptiveInformationContentEntity)
    }
    shipments.discard(None)
    assert len(shipments) == 3 and members(reasoned, IOF.Shipment) == shipments
    lots = {s for s in lifted.subjects(IOF.hasRole, None) if str(s).startswith(FUEL["lot/"])}
    assert len(lots) == 3 and lots <= members(reasoned, IOF.TraceableResourceUnit)
    # SCRO defines a lot as designated by a lot identifier, and a lot identifier as designating a
    # lot. Neither definition can fire first, so nothing is ever inferred to be either.
    assert not members(reasoned, IOF.Lot) and not members(reasoned, IOF.LotIdentifier)


def test_one_node_holds_a_tanks_fuel_for_all_time(lifted):
    t1 = FUEL["tank/ZA0001/T1/fuel"]
    parts = set(lifted.subjects(OBO.BFO_0000176, t1))
    # Both refinery shipments received, the 400,000 gal shipped out, and the sample, all parts of
    # one material entity, none of them at a stated time.
    assert len(parts) == 4


def shape(g, process):
    """A process's edges, with each neighbour reduced to its classes: what the reading says about
    it, without the names of the tank, the record, or the day."""
    out = {
        (p, frozenset(g.objects(o, RDF.type)))
        for p, o in g.predicate_objects(process)
        if p != RDF.type
    }
    into = {(p, frozenset(g.objects(s, RDF.type))) for s, p in g.subject_predicates(process)}
    return out, into


def test_a_regrade_and_a_downgrade_read_the_same(source, lifted):
    regrade, downgrade = (FUEL[f"grade-change/{c}/change"] for c in ("GC-002", "GC-003"))
    assert shape(lifted, regrade) == shape(lifted, downgrade)
    # The records tell them apart only by kind and by the sample's results.
    kinds = {
        source.value(FUEL[f"grade-change/{c}"], FUEL_RECORDS.kind) for c in ("GC-002", "GC-003")
    }
    assert kinds == {Literal("regrade"), Literal("downgrade")}


@pytest.mark.parametrize("cq", CQS, ids=[q.stem for q in CQS])
def test_cq_gives_the_recorded_verdict(lifted, cq):
    with (READING / "cq" / "expected" / f"{cq.stem}.csv").open(newline="") as fh:
        header, *expected = csv.reader(fh)
    result = lifted.query(cq.read_text())
    assert [str(v) for v in result.vars] == header
    assert graph.rows(result) == sorted(tuple(r) for r in expected)


def test_only_a_sample_that_passed_says_so(lifted):
    on_spec, off_spec = (FUEL[f"sample/{s}/material"] for s in ("S-2026-0030", "S-2026-0062"))
    assert lifted.value(on_spec, IOF.satisfiesRequirement) == FUEL["specification/MIL-DTL-5624"]
    # The downgraded fuel's sample failed the same specification, which OWL can only leave unsaid.
    assert lifted.value(off_spec, IOF.satisfiesRequirement) is None
