# Plan

Where the project is headed and what comes next. The method is in [README.md](README.md); results are in
[findings/](findings/). Update this file when the direction changes, and record the decision in
[docs/adr/](../docs/adr/) once both of us agree on it.

## Direction

**Traceability: following goods, and the records about them, through the supply chain.** Narrowed to:

- **Custody and ownership change events** (receipt, issue, transfer of accountability), not transport alone.
- **DoD logistics records**, using the synthetic `dlms_synth` source, with civilian traceability as the baseline.
- **On SCRO**, so that each result can be traced to BFO, IOF Core, or SCRO, as the method requires.

Why:

- Traceability tests BFO where it commits most: goods vs. their movement, relations over time, and wholes whose
  parts change.
- Ameri et al. built a traceability ontology (SCT) on BFO, IOF Core, and SCRO for bulk grain: transfer and
  transport events in 2022 ([[ameriEnablingTraceabilityAgriFood2022]]), then custody change, ownership change,
  sampling, observation, and transformation in 2023 ([[ameriAgriFoodSupplyChain2023]]). But the 2023 classes are
  primitive: saying the custodian before differs from the one after needs interval relations BFO's OWL release
  lacks, and re-identification is deferred because change of identity isn't formalized. What's left for us:
  - **Accountability** as a third relation besides custody and ownership: in DoD records the government keeps
    ownership while custody and accountability move between activities.
  - **Re-identification**: document numbers, transportation control numbers, NSN substitutions.
  - **Discrete, serialized items** rather than bulk grain.
  - **Whether SCRO and IOF Core alone can express this**, since SCT isn't published.
- The `dlms_synth` mapping already shows where SCRO runs out for DoD records: no requisition, due-in, acceptance, or
  discrepancy class, and no identity for stock issued from a shelf. See
  [its README](../data/mappings/dlms_synth/iof-scro/README.md#not-mapped-yet).

Not yet decided: whether this narrows [ADR-0004](../docs/adr/0004-research-method.md) (still *Proposed*) or needs an
ADR of its own.

## Next steps

1. **Write traceability CQs with expected answers.** Start from Ameri et al.'s CQs (events a load took part in
   between two times; equipment the goods passed through; which loads are blends) and adapt them to DoD records
   and to custody and ownership change. Put them in `competency-questions/`, next to CQ-001 and CQ-002.
2. **Evaluate them against SCRO on our data.** For each CQ: answerable with SCRO alone, with IOF Core, or only with
   something added. Ameri et al. needed a whole extra ontology on top of SCRO; check whether that still holds.
3. **Run the BFO analysis** on what the CQs turn up, as findings in `findings/`. Candidates:
   - **Roles that begin and end with events.** Ameri et al. treat a load as grain bearing a source or target load
     role for the length of one transfer. Compare with SCRO's shipment role ([F-001](findings/F-001.md)).
   - **Time only through events.** In their ontology objects have no times of their own, only the events they take
     part in. Relates to [F-002](findings/F-002.md).
   - **Fungible stock.** Grain mixed in a bin and stock issued from a shelf both lack an identity to trace. Does BFO
     help, or does every approach need a lot or batch identifier?