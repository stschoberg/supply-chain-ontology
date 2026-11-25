# fuel_records → IOF Core + SCRO

The first reading of the [fuel records](../README.md) ([ADR-0006](../../../../docs/adr/0006-readings-of-the-study-records.md)):
the same invented records, taken from their own terms into the IOF supply chain stack by SPARQL CONSTRUCT rules, as
the [DLMS rules](../../dlms_synth/iof-scro/README.md) take the DLMS records.

```bash
make lift-examples    # ../source.nt → lifted.ttl, after editing a rule
uv run pytest tests/test_lift_fuel_records_iof_scro.py
```

`cq/` holds the four competency questions asked in this reading's terms, and `cq/expected/` what they return: the
verdicts. The test fails if either changes.

## The rules

Each rule is one decision. **Ours** marks a decision IOF and SCRO leave open, so the reading had to make it.

| Rule | Source | IOF / SCRO | Decided by |
|---|---|---|---|
| 01 | Activity | `organization` | Core |
| 02 | Appointed officer | `person` | Core |
| 03 | Tank | an `object` (BFO) holding one `material entity` with an `industrial inventory role`, for all time | SCRO; **ours**: one node per tank |
| 04 | *(custody; no row)* | the DFSP is `agent in` a `storage process` of the tank's fuel | SCRO; **ours**: storage stands in for custody |
| 05 | Batch number on a certificate | `identifier` that `designates` a `material entity` with a `lot role` | SCRO |
| 06 | Shipment document | the fuel shipped: a `material entity` with a `shipment role`, realized in a `transport process` | SCRO |
| 07 | Refinery certificate on a shipment | the shipped fuel is `continuant part of` the refinery lot | **ours** |
| 08 | Receipt | `receiving process`; the shipped fuel is then part of the tank's fuel | SCRO; **ours**: received = shipped |
| 09 | Ship-from tank | the shipped fuel was part of the tank's fuel | **ours** |
| 10 | Certificate of analysis and its source batches | a `manufacturing process` with the old lots as `input`, the new lot as `output` | **ours**, pushed by SCRO's lot role axiom |
| 11 | Additive injection | `manufacturing process` with the tank's fuel as both `input` and `output` | **ours** |
| 12 | Grade code | `information content entity` that `classifies` the fuel, with no time | Core |
| 13 | Grade change | `change` in which the tank's fuel takes part; kind and reason unmapped | Core |
| 14 | Sample | `material entity`, part of the tank's fuel, designated by its number | BFO, Core; SCRO has no sample |
| 15 | Test result | output of a `measurement process` on the sample; value as text | Core |
| 16 | Sale | `selling business process`; the sold fuel is part of T3's fuel and `owned by` the customer | SCRO |
| 17 | DD Form 2920 | `inventory management process` with both officers as `agent in` | SCRO |
| 18 | Every date | the process `occurs on` a `temporal region` | BFO, Core |
| 19 | Sample on specification | `satisfies requirement` its fuel specification | Core |
| 20 | Appointment | an `agent role` gained and lost in dated processes, acting on behalf of the DFSP | Core |

No rule asserts a class SCRO defines (lot, shipment, traceable resource unit, classifier); the reasoner decides.

## What the reading decides

The answers to the [design note's questions](../README.md#what-each-reading-must-decide):

| Question | SCRO's answer |
|---|---|
| What material entity does a receipt, a tank's contents, or a batch correspond to? | A receipt: the shipped fuel, a shipment. A tank: one inventory node for all time. A batch: a material entity with a lot role, which is never inferred to be a lot. |
| Is T1 after event 2 one portion or two? | One, with both shipments as parts. The lots keep their roles; nothing says they ended. |
| Is CA-55 the same as, part of, or derived from RB-101? | Output of a process RB-101 was input to. The process is read off a certificate; nothing happened to the fuel. |
| Does a regrade change the material, or only how it is classified? | Neither, in the model: the same node takes part in a change and is classified by both grades. A regrade and a downgrade map identically. |
| What is sample S-2026-0041 related to, and how? | Part of T1's fuel at some time. Not how much it represents. |
| At a given time, who owns T1's contents, who has custody, and who is accountable? | No owner. Custody: the DFSP, at no particular time. Accountable: the right officer each day, but as someone acting for the DFSP, not as accountable for the fuel. |

## The competency questions

| CQ | Verdict | Why |
|---|---|---|
| [CQ-003](cq/CQ-003.rq): refinery batches in T3's fuel | **Right rows:** RB-101, RB-102 | Only through the process rule 10 makes of the certificate's source list. No material path links T3's fuel to the refinery lots: every part-of is "at some time", so sharing T1's fuel shows nothing. |
| [CQ-004](cq/CQ-004.rq): same portion after regrade, after downgrade? | **Yes to both, by construction** | One node per tank. Each is classified by both grades, with no time. The regrade and the downgrade differ only in whether one sample satisfies a specification (rule 19), and that is not linked to the change. |
| [CQ-005](cq/CQ-005.rq): which portion S-2026-0041 represents, and how much | **Part:** all of T1's fuel, at no time; **no quantity** | No term for representing, and the gallons represented are not mapped. |
| [CQ-006](cq/CQ-006.rq): owner, custody, accountable on 3/10 and 3/20 | **Some rows** | No owner: `owned by` has no time, and the DWCF is in no record. Custody: the DFSP on both days, because storage has no time. Accountable: Responsible Officer 1, then 2, from dated gain and loss of a generic agent role, compared in SPARQL. |

## Findings

1. **No lot is ever inferred.** SCRO defines `lot` as a material entity with a lot role *designated by a lot
   identifier*, and `lot identifier` as an identifier that *designates a lot*. Each needs the other first, so from
   data the reasoner concludes neither: the three lots are traceable resource units, never lots. SCRO's own
   first-order definition has only the role; the OWL adds the identifier. Shipment, defined by its role alone, is
   inferred. Checked with OWL 2 RL; since nothing forces either class, HermiT should agree (not yet run).
2. **Which, not when.** Every relation the reading uses between a portion and its whole or its grade is *at some
   time*: `continuant part of at some time`, `classifies`, `owned by`. So one node can stand for T1's fuel from
   4 February to 20 March, and the 400,000 gal shipped and the 79,603 gal left are both parts of it. Only processes
   are dated. This comes from BFO 2020's OWL release, whose parthood has only *at some time* and *at all times*
   forms; IOF adds none indexed to a time.
3. **Re-batching becomes manufacturing.** SCRO's lot role requires a manufacturing process, and SCRO has no
   blending or commingling. Reading the certificate as one answers CQ-003, by a process nobody performed.

## Limits

The rules marked ours are judgments another reading of SCRO could make differently. The findings above survive the
obvious alternatives: dating parthood would need a pattern IOF does not have, and asserting `lot` directly would
assert a defined class.
