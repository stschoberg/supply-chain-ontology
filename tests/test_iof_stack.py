"""Check the IOF tables against the committed build in research/reference/iof-scro/build/."""

import pytest

from sco import iof_stack

IOF = "https://spec.industrialontologies.org/ontology/construct/"


@pytest.fixture(scope="module")
def stack():
    return iof_stack.load()


def test_every_term_has_a_layer(stack):
    for table in (stack.classes, stack.properties):
        assert set(table["layer"]) == set(iof_stack.LAYERS)


def test_layer_is_iofs_own_tag_not_the_iri(stack):
    layer = stack.classes.set_index("IRI")["layer"]
    assert layer[IOF + "SupplierRole"] == "CORE"  # supplier is IOF Core, not SCRO
    assert layer[IOF + "DistributorRole"] == "SCRO"
    assert layer[iof_stack.BFO_IRI + "0000023"] == "BFO"  # role
    # IOF Core declares process profile under a BFO IRI and tags it as its own.
    assert layer[iof_stack.BFO_IRI + "0000144"] == "CORE"


def test_every_iof_class_has_a_bfo_ancestor(stack):
    with_bfo_ancestor = set(stack.ancestors.loc[lambda d: d["ancestor layer"] == "BFO", "IRI"])
    iof_classes = stack.classes.loc[lambda d: d["layer"] != "BFO"]
    unrooted = iof_classes.loc[lambda d: ~d["IRI"].isin(with_bfo_ancestor), "LABEL"]
    assert unrooted.empty, f"classes with no BFO ancestor: {list(unrooted)}"


def test_ancestors_are_inferred_not_just_asserted(stack):
    # No axiom states this; HermiT infers it from the two classes' definitions.
    shipment = stack.ancestors.loc[lambda d: d["IRI"] == IOF + "Shipment"]
    assert {"traceable resource unit", "material entity"} <= set(shipment["ancestor label"])


def test_nearest_bfo_category_is_the_most_specific_one(stack):
    category = iof_stack.nearest_bfo_category(stack.ancestors)
    assert category[IOF + "Shipment"] == "material entity"  # not continuant or entity
    assert category[IOF + "DistributorRole"] == "role"
    assert category[IOF + "PurchaseOrder"] == "generically dependent continuant"


def test_ancestor_depth_orders_general_to_specific(stack):
    depth = stack.ancestors.drop_duplicates("ancestor").set_index("ancestor label")[
        "ancestor depth"
    ]
    assert depth["entity"] == 0
    assert depth["entity"] < depth["continuant"] < depth["material entity"]


def test_restriction_uses_names_where_a_property_is_used_and_defined(stack):
    has_role = stack.restriction_uses.loc[lambda d: d["property"] == "has role"]
    assert set(has_role["used in"]) == {"CORE", "SCRO"}
    assert set(has_role["defined in"]) == {"CORE"}
    assert (has_role["uses"] > 0).all()


def test_axiom_types_and_fol_annotations_cover_every_layer(stack):
    disjoint = stack.axiom_types.loc[lambda d: d["axiom type"] == "DisjointClasses"]
    assert "BFO" in set(disjoint["layer"])
    assert list(stack.fol_annotations.index) == list(iof_stack.LAYERS)
    assert stack.fol_annotations["BFO"] == 0 < stack.fol_annotations["SCRO"]


def test_sparql_returns_strings_with_prefixes_predeclared():
    found = iof_stack.sparql(
        iof_stack.layer_graph("CORE"),
        "SELECT ?c WHERE { ?c a owl:Class ; rdfs:label 'supplier role'@en-US }",
    )
    assert found["c"].tolist() == [IOF + "SupplierRole"]
