# ADR-0002: Representing time and change

- **Status:** Proposed
- **Date:** 2026-10-04
- **Deciders:**

## Context

Supply chain scenarios are inherently temporal: a supplier holds a role *during* a contract, inventory levels
change, a port is closed *from* one date *to* another, and a shipment is delayed. BFO 2020 relations like
`bearer of` and `has participant` are temporally unqualified in the OWL release, so we need a pattern for facts that
hold only at certain times.

## Options

1. **Ignore time in the TBox.** Each scenario is a snapshot, and temporal facts become data properties queried in
   SPARQL. Simple, but weak on reasoning.
2. **Processes and temporal regions.** Temporal facts are tied to processes (`occupies temporal region`) and the
   processes carry the timing. Most BFO-idiomatic, and works well for supply and transport processes.
3. **Reified temporal qualification,** e.g. CCO-style or role-holding intervals. Expressive, but verbose and
   harder to reason over.

## Decision

_TBD._ This determines how disruption scenarios are modeled, so decide it before the first real-data pipeline.

## Consequences

_TBD._
