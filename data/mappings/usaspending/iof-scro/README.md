# USAspending → IOF Core + SCRO

Layer 2 of [ADR-0005](../../../../docs/adr/0005-two-layer-lifting.md) for one target: rules that take awards
from USAspending's own terms (`usas:`, layer 1) into the IOF supply chain stack pinned in
[research/reference/iof-scro/](../../../../research/reference/iof-scro/). This is the IOF model for the comparison
in [the research method](../../../../research/README.md), not our own ontology, and it doesn't decide
[ADR-0001](../../../../docs/adr/0001-mid-level-ontology.md).

It is a first trial. Product codes, competition data, and dates are not mapped yet (see below). Each data release
includes the resulting graph as `iof-scro.experimental.nt.gz`, named that way because the rules will change.

```bash
make lift             # data/graph/iof-scro.experimental.nt.gz, from the tables in data/dist/
make lift-examples    # example/source.nt → example/lifted.ttl, after editing a rule
```

| Path | What it is |
|---|---|
| `NN-*.rq` | One SPARQL CONSTRUCT rule per modeling decision. Each reads only the source graph. |
| `example/source.nt` | Five awards and their eight entities, cut from release `data-2026-10-12`'s graph. |
| `example/lifted.ttl` | What the rules make of them. `tests/test_lift_iof_scro.py` fails if it is stale. |

The example: a sole-source award, one with an NSN, an order under a parent contract, one to Canadian Commercial
Corporation (an agent, not a manufacturer), and a fully competed one.

## The rules

| Rule | Source | IOF / SCRO | Layer |
|---|---|---|---|
| 01 | Award | `purchase order` | SCRO |
| 02 | Recipient | `organization` that `has role` a `supplier role` | Core |
| 03 | Awarding sub-agency (a name) | `organization` that `has role` a `buyer role` | Core |
| 04 | Award links recipient and agency | `supply relationship`, `prescribed by` the award, with `depends on supplier` and `depends on buyer` | SCRO |
| 05 | Recipient parent | `owns` | SCRO |
| 06 | UEI, CAGE code, PIID | `organization identifier` / `identifier` that `designates` the thing, with `has text value` | Core, SCRO |
| 07 | Obligated amount | `value expression` with `has simple expression value` | Core |

## Trial notes

Research notes from the first run, kept here until they are written up as a finding.

### Predictions

Written on 2026-10-12, before the rules were run.

1. **Product kinds have no home.** IOF's `material product` is a particular physical thing, so an award's PSC and
   item name can't be attached to it. This is the "particulars, not types" row of the method's principles table,
   which predicts product codes become specification individuals.
2. **One award becomes five to eight nodes** instead of one, from the relationship, identifiers, and values.
3. **Competition data has no home.** Extent competed and offers received stay behind.

### What happened

**It fits, and the reasoner does its part.** All five awards map. Reasoning over the result with the IOF stack
(OWL 2 RL) raises no error and infers the five recipients are `supplier` and the three agencies are `buyer`,
neither of which the rules assert.

**Prediction 1 held, and nothing was done about it.** No rule maps `psc`, `itemName`, or `nsn`. The choices are to
invent a physical product per award that may never have been delivered, to invent specification individuals that
SCRO doesn't define for products, or to leave it out. We left it out. This is the decision to make next.

**Prediction 2 was too high at scale.** Nodes shared between awards are counted once.

| Per award | Source graph | IOF graph |
|---|---|---|
| Nodes, example of 5 | 2.6 | 10.4 |
| Nodes, all 38,118 awards | 1.04 | 4.16 |
| Triples, all 38,118 awards | 21.5 | 12.4 |

Four nodes are new for every award: the purchase order, its supply relationship, its identifier, and its value
expression. The IOF graph has fewer triples only because it drops 17 properties.

**Prediction 3 held, and it is wider than competition.** The rules use 8 of the source's 25 properties. Unmapped:

- Product: `psc`, `itemName`, `nsn`, `description`, `originCountry`.
- Competition: `extentCompeted`, `offersReceived`, `otherThanFullAndOpenReason`.
- Dates: `baseActionDate`, `lastModifiedAt`. An agreement is a continuant, so a date needs a process to attach to,
  and the source records none.
- Other: `parentPiid`, `domesticOrForeignEntity`, `awardKey`, `dlaReferenceNumber`, `sourceFile`, and the names as
  reported on each award.

**Not predicted: every buyer is also a customer.** The rules give agencies a `buyer role`. SCRO's
`depends on buyer` has range `customer`, so the reasoner also makes each one a `customer`: by SCRO's definition,
something that uses the product or receives the service.

**Not recorded: the currency.** Rule 07 keeps the amount, but Core has no term to say it is in US dollars.

## Limits

- **Reasoning is OWL 2 RL, not full OWL 2 DL.** A HermiT run over the stack plus the example was stopped as too slow.
  RL finds the inferences above but is not a complete consistency check.
- **Five awards are checked by hand and by tests.** The counts for all awards come from `make lift` over the full
  release (472,740 triples out).
- **Our choices, not IOF's.** Each rule is one way to use IOF's terms. `purchase order` for every award, ownership
  for "corporate parent", and a buyer role for the agency are judgments.
