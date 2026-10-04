"""Structural checks on the TBox that don't need a DL reasoner."""

from rdflib import OWL, RDF, RDFS, Graph
from rdflib.namespace import SKOS

from sco import graph
from sco.namespaces import BFO, SCO


def test_edit_file_parses():
    assert len(Graph().parse(graph.EDIT_FILE)) > 0


def test_every_sco_class_has_label_and_definition():
    g = graph.load_tbox()
    missing = [
        str(cls)
        for cls in g.subjects(RDF.type, OWL.Class)
        if str(cls).startswith(str(SCO))
        and not (g.value(cls, RDFS.label) and g.value(cls, SKOS.definition))
    ]
    assert not missing, f"classes missing label or definition: {missing}"


def test_every_sco_class_is_rooted_in_bfo():
    g = graph.reason(graph.load_tbox())
    unrooted = [
        str(cls)
        for cls in g.subjects(RDF.type, OWL.Class)
        if str(cls).startswith(str(SCO)) and (cls, RDFS.subClassOf, BFO.entity) not in g
    ]
    assert not unrooted, f"classes not under bfo:entity: {unrooted}"
