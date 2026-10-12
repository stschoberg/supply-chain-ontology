"""The layer 2 mapping of synthetic DLMS records into IOF Core + SCRO, checked on its example."""

import pytest
from rdflib import RDF, Graph
from rdflib.compare import to_isomorphic

from data import lift
from sco import graph, iof_stack
from sco.namespaces import DATA, DLMS_SYNTH, IOF, OBO

TARGET = lift.MAPPINGS_DIR / "dlms_synth" / "iof-scro"
SYNTHETIC = str(DATA["synthetic/"])


@pytest.fixture(scope="module")
def source():
    return Graph().parse(TARGET / "example" / "source.nt")


@pytest.fixture(scope="module")
def lifted():
    return Graph().parse(TARGET / "example" / "lifted.ttl")


@pytest.fixture(scope="module")
def stack():
    return Graph().parse(iof_stack.BUILD / "iof-reasoned.ttl")


@pytest.fixture(scope="module")
def reasoned(lifted, stack):
    return graph.reason(stack + lifted)


def members(g, cls):
    return {s for s in g.subjects(RDF.type, cls) if str(s).startswith(str(DATA))}


def test_example_is_up_to_date_with_the_rules(source, lifted):
    rebuilt = graph.construct(source, TARGET)
    assert to_isomorphic(rebuilt) == to_isomorphic(lifted), "run `make lift-examples` and commit"


def test_rules_use_only_terms_the_pinned_iof_release_declares(lifted, stack):
    used = {t for triple in lifted for t in triple if str(t).startswith((str(IOF), str(OBO)))}
    assert used
    assert not {t for t in used if (t, RDF.type, None) not in stack}


def test_nothing_invented_is_said_about_a_real_node(lifted):
    assert all(str(s).startswith(SYNTHETIC) for s in lifted.subjects())
    # Real nodes appear only as what a synthetic process is prescribed by: the purchase order.
    real = {o for o in lifted.objects() if str(o).startswith(str(DATA)) and SYNTHETIC not in str(o)}
    assert real and real == set(lifted.objects(predicate=IOF.prescribedBy))


def test_each_record_becomes_the_record_and_what_it_is_about(source, lifted):
    notices = set(source.subjects(RDF.type, DLMS_SYNTH.ShipmentNotice))
    assert notices == set(lifted.subjects(RDF.type, IOF.AdvanceShipmentNotice))
    for notice in notices:
        shipment = lifted.value(notice, IOF.isAbout)
        assert shipment != notice and (shipment, RDF.type, OBO.BFO_0000040) in lifted
    receipts = set(source.subjects(RDF.type, DLMS_SYNTH.Receipt))
    for receipt in receipts:
        receiving = lifted.value(receipt, IOF.describes)
        assert (receiving, RDF.type, IOF.ReceivingProcess) in lifted
        assert lifted.value(receiving, IOF.occursOn) and lifted.value(receiving, IOF.occursAt)
        # The process the receipt describes received the shipment its notice was about.
        notice = source.value(receipt, DLMS_SYNTH.shipment)
        assert lifted.value(receiving, OBO.BFO_0000057) == lifted.value(notice, IOF.isAbout)


def test_shipments_and_locations_are_inferred_not_asserted(source, lifted, reasoned):
    shipments = len(set(source.subjects(RDF.type, DLMS_SYNTH.ShipmentNotice)))
    assert not members(lifted, IOF.Shipment) and not members(lifted, IOF.ShipToLocation)
    assert len(members(reasoned, IOF.Shipment)) == shipments
    assert len(members(reasoned, IOF.TraceableResourceUnit)) == shipments
    assert members(reasoned, IOF.ShipFromLocation) and members(reasoned, IOF.ShipToLocation)
