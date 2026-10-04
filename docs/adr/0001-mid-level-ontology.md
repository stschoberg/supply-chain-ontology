# ADR-0001: Mid-level ontology between BFO and SCO

- **Status:** Proposed
- **Date:** 2026-10-04
- **Deciders:**

## Context

BFO is a top-level ontology. Modeling supply chains directly under it means reinventing organization, artifact,
facility, agent role, act, geospatial location, and so on. A mid-level ontology supplies those classes. The seed
classes in `sco-edit.ttl` currently sit directly under BFO as placeholders.

## Options

1. **Common Core Ontologies (CCO).**
   - Pros: adopted alongside BFO as a DoD/IC baseline standard. Broad coverage of agents, artifacts, facilities,
     geospatial data, information entities, and events. Large user community in defense.
   - Cons: large import. Less supply-chain-specific vocabulary.
2. **Industrial Ontologies Foundry (IOF) Core and the IOF Supply Chain ontology.**
   - Pros: BFO-based, and already models supply chain concepts (supplier, procurement, logistics). Industry and
     civilian alignment.
   - Cons: less DoD adoption. Still maturing.
3. **Both:** import CCO as the base and align or borrow supply-chain patterns from IOF.

## Decision

_TBD._

## Consequences

- Add the chosen ontology to `ontology/imports/` and `catalog-v001.xml`. Prefer `robot extract` modules over full
  imports if the full ontology is slow in Protégé.
- Re-parent `sco:Organization`, `sco:Product`, etc. under mid-level classes, or replace them with direct reuse.
