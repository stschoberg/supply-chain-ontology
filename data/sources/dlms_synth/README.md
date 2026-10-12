# dlms_synth: synthetic DoD logistics records

**Everything in this directory beyond the awards themselves is made up.** USAspending says who agreed to supply
what, from where, by when. It records no shipments. This source invents what would follow a real award, so
the parts of a supply chain ontology that awards can't reach (shipments, receipts, stock, requisitions) have
something to describe.

```bash
make transform    # builds the dlms_synth__* tables with everything else, in data/warehouse.duckdb
```

It is a source like [USAspending](../usaspending/README.md), except that it is generated, not fetched. dbt derives
it from the staged awards, in [`transform/models/dlms_synth/`](../../transform/models/dlms_synth/), so there is no
fetcher and no raw snapshot here. The name says both things: the concepts are DLMS's, and the records are synthetic.

It covers every award that bought something (a positive obligated amount). Its tables are published in each data
release, marked synthetic in their names, their descriptions, the release notes, and every row. Its graph,
`dlms_synth.nt.gz`, is in each release too.

## What is real and what is invented

| Real, from the award | Invented |
|---|---|
| The supplier and its CAGE code | That any shipment happened |
| The awarding agency | How many shipments, and how many units in each |
| The contract number and its period of performance | Every date something was shipped, received, accepted, or issued |
| The place of performance | Which depot received it, and that it was later requisitioned |
| The product class, and the NSN when the award has one | Unit price, and so every quantity |
| The names of DoD activities | Their activity codes, document numbers, and transportation control numbers |

The suppliers keep their real names. An invented late or short shipment says nothing about the real company. Every
row has `synthetic = true`, and the tables stay out of the real ones.

## The concepts are the DoD's

Synthetic data fits whatever shape generated it, so it can't show that real data fits a model. To limit that, the
shape is not ours. Each table is one transaction of the
[Defense Logistics Management Standards](https://www.dla.mil/Defense-Data-Standards/) (DLMS), the DoD's own
definition of what moves through its supply system, and the tables follow three end-to-end processes of the DoD
Business Enterprise Architecture (the 2024 federated framework).

| Table | DLMS transaction | End-to-end process | Step |
|---|---|---|---|
| *(the award, real)* | | Procure-to-Pay | Award Procurement Instrument |
| `dlms_synth__due_ins` | 527D, Pre-positioned Materiel Receipt (PMR) and Due-in Actions | Plan-to-Stock | Determine Source |
| `dlms_synth__shipment_notices` | 856P, Procurement Advance Shipment Notice (ASN) | Procure-to-Pay | Perform Receipt, Acceptance, and Return |
| `dlms_synth__acceptance_reports` | 861P, Procurement Acceptance Report | Procure-to-Pay | Perform Receipt, Acceptance, and Return |
| `dlms_synth__receipts` | 527R, Physical Receipt and Materiel Receipt Acknowledgement (MRA) | Plan-to-Stock | Receive, Accept and Warehouse Inventory |
| `dlms_synth__discrepancy_reports` | 842A/W, Standard Supply Discrepancy Report (SDR) Notifications | Procure-to-Pay | Perform Receipt, Acceptance, and Return |
| `dlms_synth__requisitions` | 511R, Requisition | Order-to-Cash | Accept Orders |
| `dlms_synth__release_orders` | 940R, Materiel Release Order (MRO) | Order-to-Cash | Fulfill Orders |
| `dlms_synth__issues` | 867I, Issue | Order-to-Cash | Fulfill Orders |
| `dlms_synth__activities` | *(lookup)* the DoD activities the records name | | |

Only each transaction's concept and main data elements are followed. The tables are not the implementation
conventions segment by segment, and the code values (supply condition `A`, priority, acceptance point) are from
general knowledge of the standards, not checked against them.

## What the records say

1. **Due-in.** The depot is told to expect the quantity the contract bought, by the end of its period of
   performance.
2. **Shipment notice.** The supplier ships, in one or two shipments, from the place of performance. Some ship after
   the period ends.
3. **Acceptance.** The government accepts the goods: at origin, by the Defense Contract Management Agency before
   they ship, for about a third of awards; otherwise at the depot after receipt.
4. **Receipt.** The depot receives them into stock, in serviceable condition.
5. **Discrepancy report.** One shipment in ten arrives short, and the depot reports it.
6. **Requisition, release order, issue.** Later the buying agency requisitions part of that stock, the depot is
   ordered to release it, and issues it.

Three things are built in on purpose, because they are where the DoD's own concepts meet the principles the
research is about:

- **Stock is not tied to a purchase.** A requisition, release order, and issue name an item and a depot, never an
  award. Once received, units from different contracts are one stock, as in the real standard.
- **Every step is an event and a record of it.** A receipt row is the 527R the depot sent, which is about the
  receiving that happened.
- **Acceptance and receipt are different things** that happen in either order, at different places, by different
  activities.

Identifiers have the real shapes: a 14-character document number (activity code, year and day, serial), a
17-character transportation control number, and a six-character activity code. Activity codes start with `Z` and
are invented; the real ones are not used.

## Reproducible

Nothing is random. Every invented value comes from a hash of the award's key and a label for what the value is
(`draw` in [`macros/dlms_synth.sql`](../../transform/macros/dlms_synth.sql)), so the same awards always give the same
tables.

## Not done yet

- Rules into IOF Core + SCRO for the records that aren't mapped yet (acceptance, discrepancies, requisitions,
  issues), and any rules into SCO. See [the mapping](../../mappings/dlms_synth/iof-scro/README.md).
- An items table that both sources refer to. The records name an item by NSN, or by product class when the award
  has no NSN, and nothing yet says those are the same item across tables.
- Contract line items beyond one per award, and direct delivery to a unit instead of a depot.
- Shipment status (856S), release confirmation (945A), and the customer's receipt acknowledgement.
- Returns, quality deficiency reports (842P), and inventory adjustments.
- A second tier: who the supplier bought from.
