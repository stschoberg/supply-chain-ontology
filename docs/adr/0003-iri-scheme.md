# ADR-0003: IRI scheme

- **Status:** Proposed
- **Date:** 2026-10-04
- **Deciders:**

## Context

Every term needs a stable IRI. Changing IRIs later breaks every query, scenario, and mapping.

## Options

1. **Readable IRIs** (`https://w3id.org/sco/SupplierRole`), as used in the current seed. Easy to read in queries and
   diffs, but renaming a class means changing its IRI.
2. **Opaque IDs** (`https://w3id.org/sco/SCO_0000001`), the OBO and CCO style. Stable across renames, but harder to
   read without label-aware tooling.

Separately: whether to register `https://w3id.org/sco/` with [w3id.org](https://github.com/perma-id/w3id.org) so the
IRIs resolve.

## Decision

_TBD._ The current seed uses option 1 with an unregistered namespace.

## Consequences

Scenario instance IRIs live under `https://w3id.org/sco/scenario/<scenario-id>/` regardless of the decision.
