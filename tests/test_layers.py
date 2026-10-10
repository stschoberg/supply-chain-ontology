"""Check the IOF layer helpers against the pinned release in research/reference/iof-scro/."""

import pytest

from sco import layers
from sco.layers import IOF, OBO


@pytest.fixture(scope="module")
def stack():
    return layers.load()


@pytest.mark.parametrize(
    ("term", "layer"),
    [
        (OBO.BFO_0000023, "BFO"),  # role
        (IOF.SupplierRole, "CORE"),  # supplier is IOF Core, not SCRO
        (IOF.DistributorRole, "SCRO"),
        (IOF.hasRole, "CORE"),
        (IOF.NotATerm, None),
    ],
)
def test_layer_is_the_declaring_file(stack, term, layer):
    assert stack.layer(term) == layer


@pytest.mark.parametrize("layer", ["CORE", "SCRO"])
def test_every_class_reaches_bfo(stack, layer):
    unrooted = [stack.label(c) for c in stack.classes(layer) if stack.path_to_bfo(c) is None]
    assert not unrooted, f"{layer} classes with no named path to BFO: {unrooted}"


def test_path_follows_the_genus_inside_an_intersection(stack):
    # factory ⊑ facility ⊓ ∃has capability.production capability: parent is in the intersection.
    path = stack.path_to_bfo(IOF.Factory)
    assert path[:2] == [IOF.Factory, IOF.Facility]
    assert stack.layer(path[-1]) == "BFO"


def test_show_path(stack):
    assert stack.show_path(IOF.DistributorRole) == (
        "distributor role [SCRO] → agent role [CORE] → role [BFO]"
    )


def test_manchester_renders_a_defined_class(stack):
    assert stack.axioms(IOF.Shipment) == [
        "shipment EquivalentTo (material entity and (has role some shipment role))"
    ]


def test_query_has_prefixes_and_can_target_one_layer(stack):
    q = "SELECT ?c WHERE { ?c a owl:Class ; rdfs:label 'supplier role'@en-US }"
    assert len(stack.query(q)) == 1
    assert len(stack.query(q, layer="SCRO")) == 0
