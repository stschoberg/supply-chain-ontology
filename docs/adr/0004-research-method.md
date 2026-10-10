# ADR-0004: How we evaluate BFO's commitments

- **Status:** Proposed
- **Date:** 2026-10-10
- **Deciders:**

## Context

The project question asks what BFO's commitments buy or cost in the supply chain domain. Building one BFO-aligned
ontology doesn't answer that on its own: our results mix BFO's commitments with our own modeling choices, and there
is nothing to compare against. IOF Core and its Supply Chain Reference Ontology (SCRO) are a published BFO-based
stack for the same domain, which gives a second case.

## Options

1. **Build SCO and report what was hard.** Cheap, but anecdotal, and every difficulty gets blamed on BFO.
2. **Trace BFO's influence through IOF Core and SCRO to instance data,** attributing each finding to the layer that
   caused it and measuring the effect on data. Then compare against a non-BFO baseline.

## Decision

Option 2, as written up in [research/README.md](../../research/README.md): findings in `research/findings/`, each
with a prediction written before looking, an attribution (BFO-forced, IOF-chosen, SCRO-specific, or SCO-chosen), and
the kind of axiom it rests on. A pinned IOF release is committed under `research/reference/iof-scro/`.

## Consequences

- Committing IOF under `research/reference/`, not `ontology/imports/`, keeps it out of SCO's TBox. It doesn't decide
  ADR-0001.
- Findings about time bear on ADR-0002 and are linked to it, but don't decide it.
- Updating the IOF release is deliberate (`IOF_RELEASE` in the Makefile), and findings may need re-checking after.
