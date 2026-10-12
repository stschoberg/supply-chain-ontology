# Mappings

Turn published tables into instance data (RDF), in two layers ([ADR-0005](../../docs/adr/0005-two-layer-lifting.md)).

```
release tables ──► layer 1: the source in its own terms ──► layer 2: SCO terms (not started)
  (data/dist/)       <source>.nt.gz, in every release
```

```bash
make dist    # build a release in data/dist/, including its layer 1 graph, <source>.nt.gz
make lift    # re-lift data/dist/'s tables into data/graph/, to try a mapping change without rebuilding
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

## Layer 2: SCO terms

Not started. Rules from the layer 1 graph into `sco:` terms, written to `scenarios/<scenario>/` so the CQ tests
and SHACL shapes run over them.
