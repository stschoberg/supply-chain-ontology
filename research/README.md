# Research

How we answer the project question: within the supply chain domain, what do BFO's specific categorial
commitments buy, or cost, relative to non-BFO approaches?

This folder holds the method (this file), the findings it produces (`findings/`), the notebooks that back them
(`notebooks/`), and the external ontologies we study (`reference/`). Modeling decisions for our own ontology
still go in [docs/adr/](../docs/adr/); background reading goes in [docs/literature/](../docs/literature/).

## The argument

```
BFO 2020        top level: domain-neutral categories and relations
   ↑ imported by
IOF Core        mid level: agents, plans, information, business processes; also supplier and buyer
   ↑ imported by
SCRO            domain level: logistics and supply chain specifics
   ↓ instantiated by
instance data   our scenarios and USAspending awards
```

1. SCRO specializes IOF Core, which specializes BFO. Every SCRO class sits under some BFO category.
2. So every supply chain fact recorded in SCRO terms is shaped by BFO's categories and relations.
3. So BFO's principles predict, in part, what instance data has to look like.
4. So we can evaluate BFO by tracing each principle down to instance data and judging what it clarifies and what it
   costs.

Step 2 is weaker than it looks, for two reasons. The rest of this method exists to handle them.

- **Not everything is BFO's doing.** IOF Core and SCRO make their own choices on top of BFO. A finding is evidence
  about BFO only when BFO forced it ([attribution](#attribution)).
- **Not everything is enforced.** OWL reasoners check only the OWL axioms. BFO's OWL release has about ten
  disjointness axioms. IOF Core and SCRO carry 313 first-order logic definitions and axioms as *annotations*, which no
  reasoner reads ([enforcement](#enforcement)).

We use IOF because it is a published, BFO-based supply chain stack. Our own ontology (SCO) is the second BFO-based
case, and a non-BFO baseline is the comparison that answers "relative to what" ([baseline](#baseline)).

## Attribution

Every finding says which layer is responsible for it. Ask these questions in order and stop at the first yes.

1. **`bfo-forced`:** could a BFO-conformant ontology make the opposite choice? If not, BFO forced it. Check against
   BFO's OWL file *and* its first-order axioms (ISO/IEC 21838-2, in `common-logic/` of the
   [BFO 2020 repo](https://github.com/BFO-ontology/BFO-2020)).
   *Example:* an information entity can't be a process. Generically dependent continuants and processes are disjoint.
2. **`iof-chosen`:** is the choice made by a term or axiom in IOF Core (`reference/iof-scro/Core.rdf`)?
   *Example:* a purchase order is an *agreement*, a kind of information content entity. BFO 2020 has no information
   content entity class at all; IOF Core adds it, then puts agreements under it.
3. **`scro-specific`:** is it made in SCRO (`SupplyChain.rdf`)?
4. **`sco-chosen`:** is it a choice in our own ontology?

The terms of IOF Core and SCRO share one namespace (`https://spec.industrialontologies.org/ontology/construct/`), so
the IRI won't tell you the layer. Check which file declares the term.

The hard cases are the useful ones. When a finding is mostly forced but partly chosen, pick the layer that made the
*decisive* choice and explain the split in the finding.

## Enforcement

Every finding says what kind of axiom it rests on:

- **`owl`:** a reasoner checks it. Violations show up as inconsistencies or wrong classifications.
- **`fol-annotation`:** written as first-order logic in an `iof-av:firstOrderLogic…` annotation. Documented, not
  checked.
- **`prose`:** only in a natural-language definition or comment.

A commitment that rests on annotations or prose costs nothing at the data layer, because nothing checks it. Count
that against claims that BFO "prevents" errors.

## Metrics

Computed per scenario, for each model of it (SCO, IOF Core + SCRO, and the baseline once it exists).

| Metric | Definition |
|--------|------------|
| Individuals per source record | Named individuals created from one source record (e.g. one USAspending award row). |
| Triples per event | Asserted triples needed to record one business event, excluding labels. |
| Query path length | Triple patterns in the SPARQL that answers a CQ, counted in the CQ's `.rq` file. |
| Inferred types | Class memberships the reasoner adds that weren't asserted (e.g. `Supplier` from a supplier role). |
| Errors caught | Deliberately bad records the reasoner or SHACL rejects, out of a fixed set of seeded errors. |
| CQ coverage | CQs the model answers correctly, out of those it is meant to answer. |

## Principles in scope

Each principle gets a notebook section and at least one finding. Predictions are written **before** looking. A
prediction that turns out wrong is a finding too.

| Principle | What it forces | Prediction | Testable against |
|-----------|----------------|------------|------------------|
| Continuant / occurrent | Goods, organizations, and documents kept apart from ordering, shipping, receiving | Clarifies: no single "order" record carrying status fields | IOF axioms; scenarios; award rows |
| Role / function / disposition | Supplier, buyer, product as roles; capability as disposition | Clarifies: one organization can supply and buy without new classes; costs a reasoner | IOF axioms; `sco:Supplier`; award rows |
| Time-indexed relations | Relations hold at a time, in BFO's first-order axioms | Costs: OWL can't record *when*, so changes of role or ownership need workarounds | BFO OWL vs. common-logic; ADR-0002 |
| Particulars, not types | Ontology classes are kinds of real things; catalog items and product codes are not | Costs: product codes become specification individuals, adding a hop to most queries | USAspending product and service codes |

**Deferred,** in favor of finishing the four above: independent vs. dependent continuants (attribute values),
specific vs. generic dependence (documents and their copies), mereology of bulk and fungible stock, and single
asserted inheritance. Move a row up when a scenario needs it.

## Baseline

"Buys or costs" only means something relative to an alternative. The baseline is a non-BFO model of the same
scenarios. GS1 EPCIS/CBV is the first candidate: event-based and widely used in supply chains. The SCOR-based model
in [@morrowDevelopingBasicFormal] is a second. We start the baseline once the four principles above have findings
from the two BFO-based models. That's also when the `models/` layout change happens.

## Threats to validity

- **Confounds:** IOF and SCO choices attributed to BFO. Handled by [attribution](#attribution).
- **One release:** findings are about IOF `Release_202603`. A later release may change them.
- **One domain:** supply chains, and only the part our data covers. USAspending records awards, not shipments or
  inspections.
- **Our own scenarios:** we wrote them, so they may favor whatever we already believed. Real data is the check.
- **Hindsight:** predictions written after looking aren't predictions. Each finding dates its prediction.

## Workflow

1. Pick a principle in scope, and write its prediction in the table above if it isn't there.
2. Explore in a [marimo](https://marimo.io) notebook under `notebooks/`: `uv run marimo edit research/notebooks/<name>.py`.
   Notebooks are plain Python files, and `make test` runs each one top to bottom.
3. Record each result as `findings/F-NNN.md`, copied from `findings/_template.md`. Link the notebook section that
   backs it.
4. If a finding bears on a CQ or an open ADR, list it in `informs:`. Don't resolve the ADR in the finding; raise it.
