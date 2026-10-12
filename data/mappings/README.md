# Mappings

Turn published tables into instance data (RDF), in two layers ([ADR-0005](../../docs/adr/0005-two-layer-lifting.md)).

```
release tables ──► layer 1: the source in its own terms ──► layer 2: a model's terms
  (data/dist/)       <source>.nt.gz, in every release          <source>.<target>.nt.gz, local only
```

```bash
make dist             # build a release in data/dist/, including its layer 1 graph, <source>.nt.gz
make lift             # lift data/dist/'s tables into data/graph/: layer 1, then every layer 2 target
make lift-examples    # regenerate each layer 2 target's example/lifted.ttl after editing its rules
```

Everything about one source is in its directory:

```
<source>/
  vocabulary.ttl     layer 1: the source's terms
  <table>.yml        layer 1: one mapping per published table
  <target>/          layer 2: rules into one model's terms, e.g. iof-scro/
    NN-*.rq
    example/         source.nt (a few real rows) and lifted.ttl (what the rules make of them)
```

## Layer 1: the source in its own terms

Each source has a directory here:

| File | What it is |
|---|---|
| `<source>/<table>.yml` | A [YARRRML](https://rml.io/yarrrml/) mapping from one published table's CSV to RDF, run by [Morph-KGC](https://morph-kgc.readthedocs.io/). |
| `<source>/vocabulary.ttl` | The classes and properties the mappings use, each with a label and definition. |

The rules:

- **Entities are decided in dbt.** A thing is a node when it has its own published table with a key. To add one,
  add the table (with key and foreign-key tests), not a clever mapping.
- **One mapping per table, and it is mechanical.** A row is a node, every column is one property named after it
  (`total_obligated_amount` → `usas:totalObligatedAmount`), and a foreign key is a link. Tests fail if a column is
  unmapped or a mapping has more than one block.
- **Codes without a table stay literals** (PSC, NSN, CAGE).
- **No interpretation.** No suppliers, products, or roles, and nothing under BFO. That's layer 2.
- **Instance IRIs come from identifiers:** `https://w3id.org/sco/data/<kind>/<identifier>`, the same in every release.
- **Missing values produce no triple.**

Prefixes in a mapping must match `sco.namespaces` (`USAS`, `DATA`).

`uv run python -m data.lift --tables <dir>` lifts any directory holding a release's files, such as a downloaded
release. Morph-KGC is fetched on first use into its own environment; it isn't a project dependency.

### Adding a source

1. `<source>/vocabulary.ttl` and a `<source>/<table>.yml` per published table, following `usaspending/`.
2. Its namespace in `sco.namespaces`, and its tables in `ROW_CLASSES` in [`lift.py`](../lift.py).
3. Tests like `tests/test_lift.py`.

## Layer 2: a model's terms

Rules from a source's layer 1 graph into the terms of one model: an ontology we want to see the data in.

| Target | Model | Status |
|---|---|---|
| [`usaspending/iof-scro/`](usaspending/iof-scro/README.md) | IOF Core + SCRO, the published BFO-based stack | First trial: parties, identifiers, amount |
| `usaspending/sco/` | Our own ontology | Not started |

The rules:

- **One SPARQL CONSTRUCT rule per modeling decision**, in a numbered `.rq` file whose name says what it claims
  (`02-recipient-is-organization-with-supplier-role.rq`). Each reads only the layer 1 graph, never another rule's
  output, so a rule can be argued about, changed, or dropped on its own.
- **Assert the least.** Give a recipient a supplier role and let the reasoner infer it is a supplier.
- **Leave out what doesn't fit**, and list it in the target's README. An unmapped property is a result.
- **Keep a small example** of real rows and what the rules make of them. Tests check it is current, uses only
  terms the target ontology declares, and gives the expected inferences.

Layer 2 graphs are written to `data/graph/` and are not part of a data release.
