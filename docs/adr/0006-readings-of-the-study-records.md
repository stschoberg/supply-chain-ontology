# ADR-0006: Reading the study records in each ontology

- **Status:** Proposed
- **Date:** 2026-11-25
- **Deciders:**

## Context

The fuel records (`data/mappings/fuel_records/`) are invented, and written to test how BFO-based ontologies track
bulk stuff. Layer 1 of [ADR-0005](0005-two-layer-lifting.md) lifts them into their own terms, and they are never
released: they are in `STUDY_ROW_CLASSES`, not `ROW_CLASSES`.

Layer 2 maps a source into a model. A model in `MODELS` gets a graph in every data release, built from every source
that has rules for it. The study needs the same records mapped into several ontologies (IOF Core with SCRO, CCO,
Keet's Stuff Ontology, and a pattern of our own) to compare what each makes of them, without publishing any of it.

## Options

1. **Add each ontology to `MODELS`.** Reuses the release pipeline, but releases the study and makes a model of
   every ontology compared.
2. **A reading per ontology, beside the records.** Each is a directory of rules under the study source, run by
   `make lift-examples` over its `source.nt` into a committed `lifted.ttl`, as the mapping examples are.
3. **A separate study pipeline,** with its own registry and outputs. More machinery for four directories.

## Decision

Option 2.

- **A reading** is a directory `data/mappings/<study source>/<ontology>/` holding SPARQL CONSTRUCT rules, as for a
  model. `data.lift.readings()` finds them; nothing registers them, and nothing in `MODELS` can reach them.
- **Its output** is `lifted.ttl` in that directory, rebuilt by `make lift-examples` and committed, so a review
  shows what each rule change does.
- **Its competency questions** are in `cq/` in that directory, one query per question in that ontology's terms,
  with what they return in `cq/expected/`. The study's questions keep their own numbers (CQ-003 to CQ-006, from
  the records' design note), apart from `competency-questions/`, which are asked of SCO's scenarios.
- **Every rule says who decided it:** BFO, the mid-level ontology, the domain ontology, or us. A rule we had to
  make, because the ontology leaves the choice open, says so.
- **No defined class is asserted,** as for the released mappings. What the ontology defines, the reasoner decides,
  and what it fails to infer is a finding.
- **Each reading takes time as its ontology does.** The SCRO reading dates processes on temporal regions, as the
  DLMS rules do. That is IOF's pattern used to test IOF, and does not decide [ADR-0002](0002-time-and-change.md).

## Consequences

- The SCRO reading is the first (`data/mappings/fuel_records/iof-scro/`). CCO, the Stuff Ontology, and the pattern
  follow the same layout. CCO needs an import pinned to a release that uses BFO 2020's IRIs, and is reasoned over
  apart from IOF.
- The readings are reasoned with OWL 2 RL in the tests. A finding that rests on what is *not* inferred should also
  be checked with HermiT.
- A reading's verdicts are tests: if a rule or the pinned ontology changes what a CQ returns, a test fails and the
  verdict has to be re-recorded on purpose.
