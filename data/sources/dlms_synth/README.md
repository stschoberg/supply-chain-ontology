# dlms_synth: synthetic DoD logistics records

**Everything in this directory beyond the awards themselves is made up.** USAspending says who agreed to supply
what, from where, by when. It records no shipments. This source invents what would follow a real award, so
the parts of a supply chain ontology that awards can't reach (shipments, receipts, stock, requisitions) have
something to describe.

```bash
make generate-dlms-synth    # example/awards.csv → example/tables/*.csv  (generate.py)
```

It is a source like [USAspending](../usaspending/README.md), except that it is generated, not fetched, and it is
built from another source's rows. The name says both things: the concepts are DLMS's, and the records are synthetic.

It is a draft covering the five awards used as the IOF mapping's example. It is not yet staged in dbt, published in
a data release, or lifted into a graph.

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
| `due_ins` | 527D, Pre-positioned Materiel Receipt (PMR) and Due-in Actions | Plan-to-Stock | Determine Source |
| `shipment_notices` | 856P, Procurement Advance Shipment Notice (ASN) | Procure-to-Pay | Perform Receipt, Acceptance, and Return |
| `acceptance_reports` | 861P, Procurement Acceptance Report | Procure-to-Pay | Perform Receipt, Acceptance, and Return |
| `receipts` | 527R, Physical Receipt and Materiel Receipt Acknowledgement (MRA) | Plan-to-Stock | Receive, Accept and Warehouse Inventory |
| `discrepancy_reports` | 842A/W, Standard Supply Discrepancy Report (SDR) Notifications | Procure-to-Pay | Perform Receipt, Acceptance, and Return |
| `requisitions` | 511R, Requisition | Order-to-Cash | Accept Orders |
| `release_orders` | 940R, Materiel Release Order (MRO) | Order-to-Cash | Fulfill Orders |
| `issues` | 867I, Issue | Order-to-Cash | Fulfill Orders |
| `activities` | *(lookup)* the DoD activities the records name | | |

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

Nothing is random at run time. Every invented value comes from a hash of the award's key, so the same awards always
give the same tables, and a test fails if the committed example is stale.

## Not done yet

- The rest of what a source has: dbt staging models (`stg_dlms_synth__<table>`), a place in data releases, and
  mappings in `data/mappings/dlms_synth/` that lift the tables into a source graph and on into IOF Core + SCRO
  and SCO, as for USAspending.
- Generating for every award, not five.
- Contract line items beyond one per award, and direct delivery to a unit instead of a depot.
- Shipment status (856S), release confirmation (945A), and the customer's receipt acknowledgement.
- Returns, quality deficiency reports (842P), and inventory adjustments.
- A second tier: who the supplier bought from.
