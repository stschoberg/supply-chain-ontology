"""Run every CQ against every scenario that has an expected-results file for it.

To add a test, write `scenarios/<name>/expected/CQ-NNN.csv`. No Python changes needed.
"""

import pytest

from sco import graph

CASES = [
    (scenario, cq)
    for scenario in graph.scenario_names()
    for cq in graph.cq_ids()
    if graph.expected_rows(scenario, cq) is not None
]


@pytest.fixture(scope="module")
def reasoned():
    cache = {}

    def get(scenario):
        if scenario not in cache:
            cache[scenario] = graph.reasoned_scenario(scenario)
        return cache[scenario]

    return get


@pytest.mark.parametrize(("scenario", "cq"), CASES, ids=[f"{s}:{c}" for s, c in CASES])
def test_cq(reasoned, scenario, cq):
    header, expected = graph.expected_rows(scenario, cq)
    result = graph.run_cq(reasoned(scenario), cq)
    assert [str(v) for v in result.vars] == header
    assert graph.rows(result) == expected
