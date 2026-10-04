from pathlib import Path

import pytest
from rdflib import Graph

from sco import graph

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("scenario", graph.scenario_names())
def test_scenario_conforms(scenario):
    conforms, report = graph.validate(graph.load_scenario(scenario))
    assert conforms, report


def test_invalid_fixture_is_rejected():
    conforms, report = graph.validate(Graph().parse(FIXTURES / "invalid-supply.ttl"))
    assert not conforms
    assert "at least one product" in report
    assert "must have a label" in report
