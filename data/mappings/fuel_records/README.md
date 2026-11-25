# fuel_records: design

Invented bulk fuel records, written by hand for the research and never released
([ADR-0006](../../../docs/adr/0006-readings-of-the-study-records.md)). The structure follows DoD procedure; the
values, codes, and events are made up, because the awards hold no fuel and the DoD's fuel systems are not public.

## Why this source exists

The research question asks whether BFO-based ontologies can track bulk stuff through the changes real
traceability involves: commingling, re-batching, regrade, sampling, and changes of custody and accountability.
BFO 2020 has no category for a portion of stuff. The ontologies built on it fill the gap in different ways:

- **SCRO**: a *lot* is a material entity that bears a *lot role*, a kind of *traceable resource unit role*. The
  material entity is otherwise unclassified, and the lot role is primitive ("the required constructs ... are
  not available in this release").
- **CCO**: *Portion of Liquid Fuel* → *Portion of Fuel* → *Portion of Material* → *Portion of Processed
  Material* → *Material Artifact* → BFO *material entity*.
- **Keet's Stuff Ontology** (EKAW 2014): kinds of stuff and amounts of stuff, refining BFO and DOLCE. Included
  only if its OWL file can be found and loads.

This source is a small set of fuel records, written once, then mapped by each of those approaches in turn. The
comparison is the set of mapping rules: the same records, read four ways.

## What the manuals show about the records

The records follow DoD Manual 4140.25 (Volumes 1, 9, and 12) and MIL-STD-3004D. Eight things about them shape
the design.

1. **No record names a portion of fuel.** Ledger transactions, physical inventories (DD Form 2921), and the
   end-of-month record (DD Form 1348-8) are kept per DFSP and product grade (Vol. 9 §4.1, §4.3, G.2). A record
   identifies a document, a tank, or a grade at a site, never a portion.
2. **Batch identity exists in four places only:** the refinery batch number on a refinery certificate of
   quality, a pipeline batch or tender number, a tanker cargo number, and a re-batch on a certificate of analysis
   after commingling (MIL-STD-3004 §3.1.9–10, §3.1.20, §3.1.94; Vol. 12 §6.3.a(5), §6.3.h(2)). It is an
   attribute of shipments and certificates, not of tanks.
3. **Every quantity is a measurement.** A quantity comes with a method (meter, tank gauge, scale), a temperature,
   an API gravity, and a gross or net value (Vol. 12 §5.2, Appendix 5A). Pipeline contents are recorded gross
   (Vol. 9 §4.1.l(3)).
4. **Three timelines disagree by design.** Gauged physical inventory, the book inventory in the ledger, and the
   documents, which are reversed and corrected when a shipment is returned or diverted (Vol. 12 §6.3.b). The
   operating gain or loss is physical minus book (Vol. 9 G.2).
5. **Grade is the classifying attribute,** and it changes only through approved events: regrade, downgrade,
   blending, reclamation (Vol. 9 §6.1; MIL-STD-3004 §3.1.38, §4.4, §5.13.7).
6. **Responsibility attaches to the account, not the fuel.** Responsible officers, terminal managers, and
   property administrators are appointed to a DFSP for a period, and hand over on a DD Form 2920 by jointly
   gauging the tanks (Vol. 9 §3.1–3.5). Ownership stays with the DWCF until the point of sale (Vol. 1 G.2,
   "capitalized fuel"). A shipment between DFSPs is "a DFSP transfer of a capitalized energy commodity and its
   accountability to another DFSP" (Vol. 12 G.2).
7. **Some status rules are proportions.** Product is in long-term storage unless at least two-thirds of the tank
   has been replaced from another source within six months (MIL-STD-3004 §5.9.1). The make-up of pipeline
   transmix is calculated from density readings into barrels of each product (MIL-STD-3004 Appendix E).
8. **Commingling the same grade leaves no record.** "Identical products may be combined in common tankage"
   after a quality check (MIL-STD-3004 §5.9.3.3). Different aviation grades may never be commingled (§5.2.1.9).

**The design rule that follows: the records layer never invents a portion.** It holds only what the
institution records. Portions, and their identity, appear in layer 2, where each approach has to decide what
the records are about. That decision is what the comparison measures.

## Layout

The two layers of [ADR-0005](../../../docs/adr/0005-two-layer-lifting.md), as for the other sources:

```
tables/*.csv              the records, hand-written
<table>.yml, schema.ttl   layer 1: a row is a node, in this source's own terms
source.nt                 layer 1's output
iof-scro/                 layer 2: the SCRO reading (rules, lifted.ttl, cq/)
```

Further readings (CCO, the Stuff Ontology, the pattern) go beside `iof-scro/`. `make lift-examples` rebuilds
`source.nt` and every reading.

In layer 1 every node is a row of a table. Batch numbers stay literals, because no record is a batch, and
nothing is a portion of fuel. Instances live under `d:synthetic/fuel/`; the terms are in the `fuel_records:`
namespace.

## The record tables

Each row of each table cites the manual section it follows in a `follows` column. Codes follow the
`dlms_synth` conventions: an invented DoDAAC starts with `Z`, and every row has `synthetic = true`. Activity
names are invented except DLA Energy's. Grade codes are `JAA` (Jet A), `JP5`, and `JP8`.

| Table | Real form or system | Fields | Case |
|---|---|---|---|
| `activities` | DFSPs (Vol. 9 Table 1) and the other parties | DoDAAC, name, kind (DFSP, refinery, laboratory, inventory manager, customer), operation, capitalized | 4 |
| `tanks` | Certified strapping chart (Vol. 12 §5.2.b(4)) | tank, DFSP, capacity in gallons, grade stored | all |
| `appointments` | RO, TM, and PA appointment letters (Vol. 9 §3.1–3.3) | person, role, DFSP, start, end | 4 |
| `account_transfers` | DD Form 2920 (Vol. 9 §3.5) | DFSP, outgoing and incoming officer, date, net inventory per tank | 4 |
| `shipments` | DD Form 1348-7, iRAPT receiving report, DD Form 250-1 (Vol. 12 §6.3.a) | document number (DoDAAC, Julian date, product code, sequence), order or STO number, grade, gross and net gallons, temperature, API gravity, determination method, from (and tank) and to, mode, batch or cargo number, certificate, seal numbers, date | 1 |
| `receipts` | DLA Form 2046, DD Form 250 (Vol. 12 §5.3, Appendix 5A) | shipment document number, receipt tank, opening and closing measurements, temperature, API gravity, gross and net gallons, in-transit variance (%) | 1 |
| `ledger_transactions` | BLSA ledger entries (Vol. 9 §4.1–4.3, G.2) | DFSP, grade, date, type (receipt, sale, shipment, regrade in or out, determinable gain or loss, physical inventory adjustment, EOM operating gain or loss), gallons, document number, reverses (the document it corrects) | 1, 2 |
| `certificates` | RCQ, CoA, recertification and release certificates (MIL-STD-3004 §3.1.20, §3.1.92, §3.1.94, §3.1.96) | kind, batch number, issuer, date, sample | 1 |
| `certificate_sources` | The same certificates | certificate, a batch number it was re-batched from (one row each) | 1 |
| `samples` | Sample log (MIL-STD-3004 §4.2.1.5.2) | sample number, where taken (tank, truck, or line), sample type, date, taken by, reason, grade, specification, gallons represented, lab report number, status | 3 |
| `test_results` | Laboratory report (MIL-STD-3004 §3.1.121, §4.2.2, Tables I–VII) | sample, test type (A, B-1, B-2, B-3, C), property, value, unit, specification limit, IGRL limit, result against each | 2, 3 |
| `grade_changes` | Disposition request and approval (Vol. 9 §6.1; MIL-STD-3004 §4.4, §5.13) | tank, grade from, grade to, kind (additization, regrade, downgrade), reason, sample, approved by, date | 2 |
| `additive_injections` | Injection records (Vol. 12 §5.4; MIL-STD-3004 §5.8) | tank, additive, additive gallons, target concentration, fuel gallons, date | 2 |
| `sales` | Point of sale (Vol. 1 G.2; Vol. 9 §5.2.d) | DFSP, tank, customer DoDAAC, grade, gallons, date | 4 |

## The story

The rows tell one story, built so each case of the analysis occurs once.

Quantities are net gallons at 60°F. ZA0001 is government-operated, so it has a responsible officer; ZB0002 is
contractor-operated, so it has a terminal manager and a property administrator (Vol. 9 Table 1).

| # | Date (2026) | Event | Case | Records |
|---|---|---|---|---|
| 1 | Feb 2–4 | Refinery batch RB-101 of Jet A (200,000 gal shipped) arrives at ZA0001 by barge, cargo CG-2601, and is received into tank T1 (199,640 gal, −0.18%). | 1 | `shipments`, `receipts`, `certificates` |
| 2 | Feb 5–6 | Batch RB-102 (280,000 gal) arrives by commercial pipeline, tender PB-7781, into the same tank (279,580 gal, −0.15%). T1 holds 479,220 gal. Nothing records that the batches are now mixed. | 1 | same |
| 3 | Feb 9 | 383 gal of FSII is injected into T1 (0.08% by volume). The ledger moves T1's fuel from Jet A to JP-8. | 2 (additization) | `additive_injections`, `grade_changes`, `ledger_transactions` |
| 4 | Feb 10 | Sample S-2026-0041, a single-tank composite representing all 479,603 gal in T1, passes a type B-1 test. | 3 | `samples`, `test_results` |
| 5 | Feb 15–19 | 400,000 gal ships from T1 to ZB0002 by pipeline, document ZA00016046J801, batch PB-7790, into tank T3 (398,900 gal, −0.275%). The shipment is first keyed as 40,000, reversed, and re-entered. Sample S-2026-0057 passes, and certificate of analysis CA-55 re-batches the fuel from RB-101 and RB-102. | 1 | `shipments`, `receipts`, `ledger_transactions`, `samples`, `certificates`, `certificate_sources` |
| 6 | Mar 2 | T2's 300,000 gal of JP-5, on specification (sample S-2026-0030, flash point 62°C), is regraded to JP-8 to meet a requirement. The fuel does not change. | 2 (regrade) | `grade_changes`, `ledger_transactions` |
| 7 | Mar 5–12 | T4's 120,000 gal of JP-5 fails flash point (58°C against a minimum of 60°C, sample S-2026-0062) and is downgraded to JP-8 (minimum 38°C). | 2 (downgrade) | `samples`, `test_results`, `grade_changes`, `ledger_transactions` |
| 8 | Mar 15 | At ZA0001, P-001 hands the account to P-002 on DD Form 2920: T1 79,603, T2 300,000, T4 120,000 gal of JP-8. No fuel moves. | 4 | `account_transfers`, `appointments` |
| 9 | Mar 20 | 20,000 gal of JP-8 from T3 is sold to unit ZU0101. Ownership passes from the DWCF. | 4 | `sales`, `ledger_transactions` |

Events 6 and 7 are the same change of grade, JP-5 to JP-8, made for different reasons. Only the sample results
tell a regrade from a downgrade.

### Where the story goes beyond the manuals

- **Additization in the ledger.** The manuals do not say how injecting FSII into Jet A is entered in the
  ledger. The records use a regrade out of Jet A and a regrade in to JP-8 that includes the additive's volume.
- **Who owns the fuel.** No record states an owner. Ownership follows from the rule that capitalized fuel
  belongs to the DWCF until the point of sale (Vol. 1 G.2), so `activities` marks the two DFSPs as capitalized,
  and the sale is the only ownership change.
- **Limits.** Specification and receipt limits are read from MIL-STD-3004D Table I; check them there before
  quoting them.
- **No NSNs.** The shipment documents carry one (Vol. 12 §6.3.a(1)), but no stock number in these records has
  been checked against the catalog, so the column is left out.
- **Empty tanks.** T1 and T3 start empty, so the only fuel mixed in T1 is the two batches.

## What each reading must decide

Layer 2 rules have to answer these. The answers are the comparison, recorded in each reading's README.

- What material entity does a receipt, a tank's contents, or a batch correspond to?
- Is T1 after event 2 one portion or two?
- Is CA-55 the same as, part of, or derived from RB-101?
- Does a regrade change the material, or only how it is classified?
- What is sample S-2026-0041 related to, and how?
- At a given time, who owns T1's contents, who has custody, and who is accountable?

## Competency questions

| CQ | Question | Case |
|---|---|---|
| CQ-003 | Which refinery batches contributed to the fuel now in T3? | 1 |
| CQ-004 | Is T2's fuel after the regrade the same portion as before? And T4's after the downgrade? | 2 |
| CQ-005 | Which portion does sample S-2026-0041 represent, and how much? | 3 |
| CQ-006 | On 2026-03-10 and on 2026-03-20, who owned, who had custody of, and who was accountable for T1's contents? | 4 |

Each approach has its own vocabulary, so each CQ gets one query per reading, in its `cq/` directory. Expected
results record the verdict: the right rows, some of them, none, or no query at all with a note in the CQ saying
why the question cannot be asked in that vocabulary.

## Open questions

1. **CCO import.** Pin a tagged release and confirm it uses the BFO 2020 IRIs in `ontology/imports/bfo-core.owl`.
   CCO and IOF are never merged; each reading is reasoned over separately.
2. **The Stuff Ontology.** Its OWL file is at [meteck.org/stuff.html](http://www.meteck.org/stuff.html), aligned
   to BFO 1.1, not BFO 2020. A reading needs a new alignment, or it is described in the article, not tested here.
3. **More tables.** A product change record (MIL-STD-3004 Appendix E) would show the institution working out a
   mixture's make-up from measurements. Physical inventories and EOM records (DD Forms 2921, 1348-8) would show
   the book against physical gap.
