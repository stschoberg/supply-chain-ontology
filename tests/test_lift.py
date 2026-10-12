"""Lift a fixture release into RDF and check it against the tables, mapping, and vocabulary."""

import csv
import gzip
import re

import pytest
import yaml
from rdflib import OWL, RDF, RDFS, XSD, Graph, Literal
from rdflib.namespace import SKOS

from data import lift, release
from sco import graph
from sco.namespaces import DATA, IOF, USAS

FIXTURE_SNAPSHOT = graph.ROOT / "tests" / "fixtures" / "usaspending"
MAPPINGS = sorted((lift.MAPPINGS_DIR / "usaspending").glob("*.yml"))
VOCABULARY = lift.MAPPINGS_DIR / "usaspending" / "vocabulary.ttl"


@pytest.fixture(scope="module")
def tables(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist")
    release.main(
        ["build", "--tag", "data-test", "--out", str(out),
         "--snapshot", f"usaspending={FIXTURE_SNAPSHOT}"]
    )  # fmt: skip
    return out


@pytest.fixture(scope="module")
def lifted(tables):
    return tables / "usaspending.nt.gz"  # a release build lifts its own tables


@pytest.fixture(scope="module")
def g(lifted):
    return Graph().parse(data=gzip.decompress(lifted.read_bytes()), format="nt")


@pytest.fixture(scope="module", params=MAPPINGS, ids=lambda p: p.stem)
def mapping_file(request):
    return request.param


def award(g, piid):
    return g.value(predicate=USAS.piid, object=Literal(piid))


def test_every_award_row_is_lifted(g):
    assert len(set(g.subjects(RDF.type, USAS.Award))) == 8


def test_foreign_keys_become_links_and_other_columns_literals(g):
    a = award(g, "SPRTA123P0105")
    assert g.value(a, USAS.nsn) == Literal("3110009898923")
    assert isinstance(g.value(a, USAS.psc), Literal)
    recipient = g.value(a, USAS.recipient)
    assert recipient == DATA[f"uei/{g.value(recipient, USAS.uei)}"]
    assert g.value(recipient, USAS.name) == g.value(a, USAS.recipientName)


def test_every_link_reaches_a_row_of_the_entities_table(g):
    entities = set(g.subjects(RDF.type, USAS.Entity))
    assert entities
    for link in (USAS.recipient, USAS.recipientParent):
        assert set(g.objects(predicate=link)) <= entities


def test_missing_values_produce_no_triples(g):
    assert g.value(award(g, "SPMYM123P0797"), USAS.nsn) is None
    assert not [t for t in g.subjects() if re.search(r"/(None|nan|null)?$", str(t))]
    assert not [o for o in g.objects() if isinstance(o, Literal) and str(o) in ("", "None", "nan")]


def test_values_are_typed(g):
    a = award(g, "SPE4A022P0831")
    assert g.value(a, USAS.totalObligatedAmount).datatype == XSD.decimal
    assert g.value(a, USAS.baseActionDate).datatype == XSD.date
    assert g.value(a, USAS.lastModifiedAt).datatype == XSD.dateTime
    assert g.value(a, USAS.lastModifiedAt).value is not None  # a valid xsd:dateTime
    assert g.value(a, USAS.dlaReferenceNumber) == Literal("8509067712")


def test_lifting_is_deterministic(tables, lifted, tmp_path):
    assert lift.lift("usaspending", tables, tmp_path).read_bytes() == lifted.read_bytes()


def test_each_target_model_gets_its_own_graph(lifted, tmp_path):
    path = lift.lift_targets("usaspending", lifted, tmp_path)["iof-scro"]
    assert path.name == "usaspending.iof-scro.experimental.nt.gz"  # the name says it's unsettled
    first = path.read_bytes()
    iof = Graph().parse(data=gzip.decompress(first), format="nt")
    assert len(set(iof.subjects(RDF.type, IOF.PurchaseOrder))) == 8
    assert lift.lift_targets("usaspending", lifted, tmp_path)["iof-scro"].read_bytes() == first


def test_mapping_uses_the_shared_namespaces(mapping_file):
    prefixes = yaml.safe_load(mapping_file.read_text())["prefixes"]
    assert prefixes["usas"] == str(USAS)
    assert prefixes["d"] == str(DATA)


def test_mapping_is_one_block_covering_every_column_of_its_table(mapping_file, tables):
    with (tables / f"{mapping_file.stem}.csv").open(newline="") as fh:
        columns = set(next(csv.reader(fh)))
    assert len(yaml.safe_load(mapping_file.read_text())["mappings"]) == 1
    assert columns == set(re.findall(r"\$\((\w+)\)", mapping_file.read_text()))


def test_vocabulary_defines_exactly_the_mapped_terms():
    vocabulary = Graph().parse(VOCABULARY)
    mapped = {
        USAS[term.removeprefix("usas:")]
        for mapping_file in MAPPINGS
        for m in yaml.safe_load(mapping_file.read_text())["mappings"].values()
        for predicate, obj, *_ in m["po"]
        for term in (obj if predicate == "a" else predicate,)
    }
    defined = {
        s
        for kind in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty)
        for s in vocabulary.subjects(RDF.type, kind)
    }
    assert mapped == defined
    for term in defined:
        assert vocabulary.value(term, RDFS.label) and vocabulary.value(term, SKOS.definition), term
