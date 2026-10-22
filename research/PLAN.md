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
- Ameri et al. (JCISE 2022) built a traceability ontology (SCT) on BFO and SCRO for bulk grain, covering transfer
  and transport events. Their 2023 follow-up (IDETC-CIE 2023, grain elevator to processor) adds transform,
  sampling, observation, custody change, and ownership change events, so custody and ownership change are not an
  open gap. What's left for us: those events in DoD records (discrete, serialized or NSN-managed items, requisitions
  against one's own supply system, government accountability), and whether SCRO itself, not SCT, can express them.
  Read the 2023 paper before settling this.
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