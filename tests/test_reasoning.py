"""Check that specific inferences happen and that unwarranted ones don't."""

from rdflib import RDF, URIRef

from sco import graph
from sco.namespaces import SCO

S01 = "https://w3id.org/sco/scenario/s01/"


def test_supplier_is_inferred_not_asserted():
    acme = URIRef(S01 + "acme")
    assert (acme, RDF.type, SCO.Supplier) not in graph.load_scenario("s01-single-source")
    assert (acme, RDF.type, SCO.Supplier) in graph.reasoned_scenario("s01-single-source")


def test_organization_without_supplier_role_is_not_a_supplier():
    delta = URIRef(S01 + "delta")
    assert (delta, RDF.type, SCO.Supplier) not in graph.reasoned_scenario("s01-single-source")
