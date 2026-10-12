"""The trial mapping of sample awards into IOF Core + SCRO terms (research/iof-lift/)."""

import pytest
from rdflib import RDF, Graph
from rdflib.compare import to_isomorphic

from sco import graph, iof_stack
from sco.namespaces import DATA, IOF

LIFT_DIR = graph.ROOT / "research" / "iof-lift"


@pytest.fixture(scope="module")
def lifted():
    return Graph().parse(LIFT_DIR / "build" / "sample.ttl")


@pytest.fixture(scope="module")
def stack():
    return Graph().parse(iof_stack.BUILD / "iof-reasoned.ttl")


@pytest.fixture(scope="module")
def reasoned(lifted, stack):
    return graph.reason(stack + lifted)


def test_build_is_up_to_date_with_the_rules_and_sample(lifted):
    source = Graph().parse(LIFT_DIR / "sample" / "usaspending.nt")
    rebuilt = graph.construct(source, LIFT_DIR / "rules")
    assert to_isomorphic(rebuilt) == to_isomorphic(lifted), "run `make research-lift` and commit"


def test_rules_use_only_terms_the_pinned_iof_release_declares(lifted, stack):
    used = {t for triple in lifted for t in triple if str(t).startswith(str(IOF))}
    assert used
    assert not {t for t in used if (t, RDF.type, None) not in stack}


def test_every_award_becomes_a_purchase_order_with_a_supply_relationship(lifted):
    orders = set(lifted.subjects(RDF.type, IOF.PurchaseOrder))
    assert len(orders) == 5
    for order in orders:
        relationship = lifted.value(order, IOF.prescribes)
        assert lifted.value(relationship, IOF.dependsOnSupplier)
        assert lifted.value(relationship, IOF.dependsOnBuyer)


def test_suppliers_and_buyers_are_inferred_not_asserted(lifted, reasoned):
    def members(g, cls):
        return {s for s in g.subjects(RDF.type, cls) if str(s).startswith(str(DATA))}

    assert not members(lifted, IOF.Supplier) and not members(lifted, IOF.Buyer)
    assert len(members(reasoned, IOF.Supplier)) == 5
    assert len(members(reasoned, IOF.Buyer)) == 3
    # `depends on buyer` ranges over customer, so SCRO also makes every buyer a customer.
    assert members(reasoned, IOF.Customer) == members(reasoned, IOF.Buyer)
