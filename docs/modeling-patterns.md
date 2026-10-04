# Modeling patterns

Recurring patterns we use, so the ontology stays consistent. Add one here whenever a choice comes up twice.

## Roles, not subclasses, for things that depend on context

An organization is not a supplier by nature. It is a supplier because it bears a **supplier role** that is realized in
**supply processes**. So:

```
org  ──bearer of──►  supplier role  ──has realization──►  supply process  ──has participant──►  product
```

`sco:Supplier` is a *defined* class (organization ⊓ ∃bearer of.SupplierRole). Never assert it; let the reasoner
infer it. The same pattern applies to customer, carrier, manufacturer, and so on.

## Product types vs. product instances

OWL individuals are **particulars**: this lot of magnets, this truck, this shipment. Product *types* such as "NdFeB
magnet" or an NSN/SKU are **classes**, or information content entities that
describe them. Don't model an SKU as an individual of `sco:Product`.

## Open world vs. closed world

| Question | Tool |
|----------|------|
| Is this organization a supplier? (classification) | OWL reasoner |
| Is this record missing a required field? | SHACL (`shapes/`) |
| How many suppliers does this product have? Is there no alternative? | SPARQL over the reasoned graph |

OWL will never conclude that something doesn't exist just because it isn't in the data.
