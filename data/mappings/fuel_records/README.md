# fuel_records

Invented bulk fuel records, used to test how a BFO-based supply chain ontology (SCRO) traces bulk stuff
through mixing, re-batching, regrading, sampling, and changes of custody. The records follow DoD Manual 4140.25
(Vols. 1, 9, 12) and MIL-STD-3004D, and every row cites the section it follows in its `follows` column. The
values and events are made up: the DoD's fuel systems are not public. Never in a data release
([ADR-0006](../../../docs/adr/0006-readings-of-the-study-records.md)).

## The story

Nine events at two fuel support points (DFSPs), February–March 2026, built so each traceability case occurs once.
Quantities are net gallons.

| # | Date | Event | Case |
|---|---|---|---|
| 1 | Feb 2–4 | Refinery batch RB-101 of Jet A arrives at ZA0001 by barge and goes into tank T1 (199,640 gal). | mixing |
| 2 | Feb 5–6 | Batch RB-102 arrives by pipeline into the same tank (279,580 gal). Nothing records that the two are now mixed. | mixing |
| 3 | Feb 9 | 383 gal of additive (FSII) is injected into T1, which turns Jet A into JP-8. | grade change |
| 4 | Feb 10 | Sample S-2026-0041, standing for all 479,603 gal in T1, passes its test. | sampling |
| 5 | Feb 15–19 | 400,000 gal ships from T1 to tank T3 at ZB0002. A certificate re-batches it as CA-55, "from RB-101 and RB-102". | re-batching |
| 6 | Mar 2 | T2's JP-5, on specification, is **regraded** to JP-8 to meet a need. The fuel does not change. | grade change |
| 7 | Mar 5–12 | T4's JP-5 fails its flash point test and is **downgraded** to JP-8. | grade change |
| 8 | Mar 15 | ZA0001's responsible officer hands the account to a successor (DD Form 2920). No fuel moves. | accountability |
| 9 | Mar 20 | 20,000 gal from T3 is sold to a unit. Ownership passes from the DWCF. | ownership |

Events 6 and 7 are the same change on paper, JP-5 to JP-8; only the sample results tell them apart.

## The data

The 14 tables in [tables/](tables/) are the records the manuals describe:

- **Movements:** shipments, receipts, ledger transactions, sales.
- **Quality:** certificates (and the batches a certificate re-batches from), samples, test results.
- **Changes:** grade changes, additive injections.
- **Who's responsible:** activities (DFSPs and other parties), tanks, officer appointments, account transfers.

What the manuals show, and the records keep:

- **No record names a portion of fuel.** Records name a document, a tank, or a grade at a site.
- **A batch number is on shipments and certificates, never on a tank.** Mixing the same grade in a tank leaves no
  record at all (MIL-STD-3004 §5.9.3.3).
- **Grade changes only by approved events,** and a regrade and a downgrade are entered the same way in the ledger.
- **Responsibility attaches to the account, not the fuel.** Officers are appointed to a DFSP, and the fuel is owned
  by the DWCF until it is sold.

[`test_fuel_records.py`](../../../tests/test_fuel_records.py) checks the tables agree with each other: quantities
balance, keys resolve, the handover totals match the books.

## The SCRO mapping

Two steps, as for the other sources ([ADR-0005](../../../docs/adr/0005-two-layer-lifting.md)):

1. **Records into RDF, as they are:** [`<table>.yml`](tanks.yml) turns each row into a node, giving
   [source.nt](source.nt). Nothing is a portion of fuel or a batch yet, because no record is one.
2. **Into IOF Core and SCRO:** the rules in [iof-scro/](iof-scro/README.md) decide what the records are about, one
   decision per rule, each marked as SCRO's or ours. Output: [iof-scro/lifted.ttl](iof-scro/lifted.ttl). What
   the mapping shows (no lot is ever inferred; parthood has no time; a regrade and a downgrade come out the same)
   is in the [SCRO reading](iof-scro/README.md).

`make lift-examples` rebuilds both.
