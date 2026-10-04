# S01: Single-source supplier (seed scenario)

A minimal, hand-written scenario that exercises the build and test pipeline end to end.

## Narrative

- **Acme Magnetics** is the only organization that supplies NdFeB magnet lot 1.
- **Beta Bearings** and **Gamma Industrial** both supply bearing lot 1.
- **Delta Logistics** is an organization that bears no supplier role.

## What it tests

| CQ | Expectation |
|----|-------------|
| [CQ-001](../../competency-questions/CQ-001.md) | Acme, Beta, and Gamma are *inferred* to be suppliers; Delta is not. |
| [CQ-002](../../competency-questions/CQ-002.md) | Magnet lot 1 is single-sourced; bearing lot 1 is not. |

Expected results live in `expected/CQ-NNN.csv`. The test suite runs every CQ that has an
expected-results file against this scenario's reasoned graph.
