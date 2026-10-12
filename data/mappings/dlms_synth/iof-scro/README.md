# dlms_synth → IOF Core + SCRO

Layer 2 of [ADR-0005](../../../../docs/adr/0005-two-layer-lifting.md): rules that take the **synthetic** DoD
logistics records from their own terms (`dlms_synth:`, layer 1) into the IOF supply chain stack. Their output goes
into the same model graph as the [USAspending rules](../../usaspending/iof-scro/README.md),
`iof-scro.experimental.nt.gz`, which is therefore part real and part synthetic. Every statement these rules make is
about a node under `https://w3id.org/sco/data/synthetic/`; they refer to a real node only as the purchase order a
synthetic process is prescribed by.

This is where SCRO's own vocabulary applies for the first time. The awards used 2 of its classes; shipments,
transport, receiving, and locations had nothing to describe.

```bash
make lift             # data/graph/iof-scro.experimental.nt.gz, from the tables in data/dist/
make lift-examples    # example/source.nt → example/lifted.ttl, after editing a rule
```

`example/` holds the synthetic records generated for the five awards in the USAspending example, and what the rules
make of them. `tests/test_lift_dlms_synth_iof_scro.py` fails if it is stale.

## The rules

| Rule | Source | IOF / SCRO | Layer |
|---|---|---|---|
| 01 | Shipment notice | `Advance Shipment Notice` that `is about` a shipment | SCRO |
| 02 | *(the shipment itself; no row of its own)* | `material entity` that `has role` a `shipment role` | BFO, SCRO |
| 03 | Transportation control number | `identifier` that `designates` the shipment | Core |
| 04 | *(the movement; no row of its own)* | `transport process` with the shipment as participant, `starts at` and `ends at` a site, `prescribed by` the purchase order, realizing the shipment role | SCRO |
| 05 | Ship-from city and country; the depot | `geospatial site` with a `ship from` or `ship to location role` | SCRO |
| 06 | Activity | `organization` | Core |
| 07 | Activity that stores materiel | also a `storage facility`, located in a site, available to the organization | SCRO |
| 08 | Receipt | `descriptive information content entity` that `describes` a `receiving process`, with the shipment as participant and the depot as agent | Core, SCRO |
| 09 | Receipt date | the receiving process `occurs on` a `temporal region` with a `temporal instant value expression` | BFO, Core |

Reasoning over the example with the IOF stack (OWL 2 RL) raises no error and infers what the rules don't assert:
that each shipped thing is a `shipment` and a `traceable resource unit`, and that the sites are `ship from` and
`ship to` locations.

## What the rules had to add

Three things the source has no row for, because a table of transactions doesn't need them:

- **The shipment.** The source has a notice about a shipment and a receipt of one, but no shipment. Here it is a
  material thing, distinct from both records.
- **The movement.** Nothing in the source is the transporting. The role SCRO gives a shipment can only be
  realized in a transport process, so one is added per shipment.
- **The place, the building, and the organization.** The source uses one activity code for all three. Here a depot
  is an organization, a storage facility, and a site.

And every record splits in two: the record, and what it is a record of.

## Not mapped yet

- **Acceptance reports and discrepancy reports.** SCRO has no acceptance, inspection, or discrepancy class.
- **Requisitions, release orders, and issues.** SCRO has a purchase order, which is an agreement between a buyer
  and a seller. A requisition against stock is a request to one's own supply system, and stock on a shelf has no
  identity of its own to issue from.
- **Due-ins.** A statement of what is expected.
- **Quantities, units of issue, and condition codes**, and the item (NSN or product class), for the same reason the
  awards' product codes are unmapped.
- **Ship dates.** A transport process has a start and an end, not one date; only the receipt date is mapped.

## Limits

- **Synthetic.** These rules show whether SCRO can describe records shaped like the DoD's. They say nothing about
  whether real DoD records would fit.
- **Reasoning is OWL 2 RL**, on the example only, as for the USAspending rules.
- **Our choices, not IOF's.** A receipt as a descriptive information content entity, a depot as three things, and
  the purchase order as what prescribes a receiving process are judgments.
