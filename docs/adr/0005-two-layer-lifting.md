# ADR-0005: Lifting tabular data to RDF in two layers

- **Status:** Proposed
- **Date:** 2026-10-12
- **Deciders:**

## Context

The data releases are tables. To test the ontology against them, their rows have to become instance data (RDF).
`data/mappings/` was reserved for this, with the method left open (Python, SPARQL CONSTRUCT, or RML).

The tables don't say what the ontology's classes need. A USAspending award is a commitment to buy a kind of part,
but `sco:SupplyProcess` and `sco:Product` are about deliveries and particular items. A mapping straight from rows to
SCO would bury modeling claims ("a recipient is a supplier", "a PSC is a product kind") inside mapping code, where
they are hard to review and hard to attribute to BFO, a mid-level ontology, or us ([ADR-0004](0004-research-method.md)).

## Options

1. **One step: tables → SCO.** What most projects do once their tables are shaped one per entity. One mapping, but it mixes mechanical translation with modeling decisions, and the
   non-BFO baseline has to be built separately.
2. **Two layers.** First lift each source into RDF in its own terms, with no interpretation. Then map that graph
   into a model's terms (SCO, or IOF Core + SCRO for comparison) with explicit rules.
3. **Virtualize** (query the tables through SPARQL-to-SQL rewriting, e.g. Ontop). Suited to large, changing
   databases. Ours are small immutable snapshots, and rewriting limits reasoning to OWL 2 QL, which can't express a
   defined class like `sco:Supplier`.

## Decision

Option 2.

**Layer 1: the source in its own terms.** Each source gets a vocabulary under `https://w3id.org/sco/source/<source>/`
(`usas:` for USAspending) and a declarative mapping (YARRRML, run by Morph-KGC) in `data/mappings/<source>/`.

- **Entities are decided in dbt, not in the mapping.** Something is an entity when it has its own published table
  with a key: `stg_usaspending__awards` (one row per award) and `entities` (one row per UEI, recipients and
  corporate parents). dbt tests guard the keys and the foreign keys between them.
- **The mapping is mechanical.** One mapping per table, named after it. A row is a node, every column is one
  property, and a foreign key is a link to the other table's node. Nothing is renamed into supply chain terms.
- Identifiers and codes without a table stay literals, however much they look like things: PSC, NSN, CAGE code,
  parent PIID, country. To make one a node, add its table (e.g. PSCs with their descriptions from the PSC manual).
- Derived columns are marked in their definitions. The NSN is parsed from free text by staging.
- Source vocabularies are not part of the SCO TBox and make no BFO claims.

**Layer 2: the lift into a model.** SPARQL CONSTRUCT rules from the layer 1 graph into one model's terms, in
`data/mappings/<source>/<target>/`. Each rule is one modeling decision. The first target is IOF Core + SCRO
(`iof-scro/`), for the comparison in [ADR-0004](0004-research-method.md). The target for our own ontology (`sco/`)
is not built yet; its rules are recorded in ADRs where they aren't obvious.

**Instance IRIs** are built from the identifier, not the source or release: `https://w3id.org/sco/data/uei/<uei>`,
`.../award/<award_key>`. The same supplier is the same node in every release and
in any later source that reports its UEI.

## Consequences

- Every data release includes `<source>.nt.gz`, lifted from its own tables. The output is deterministic, and a
  check fails the build if any row is lost. `make lift` re-lifts an existing release's tables.
- The layer 1 graph is the non-BFO baseline that ADR-0004 calls for, and the layer 2 rules are a direct record of
  what aligning to SCO adds.
- Morph-KGC runs as a pinned tool in its own environment, like ROBOT, because its dependency pins conflict with the
  project's.
- This doesn't decide [ADR-0001](0001-mid-level-ontology.md) or [ADR-0002](0002-time-and-change.md). Mapping into
  IOF terms is a comparison, not an adoption. Layer 2 for SCO needs both: an award has no class to sit under until a mid-level ontology is chosen, and its dates need a pattern.
- [ADR-0003](0003-iri-scheme.md) put scenario instances under `https://w3id.org/sco/scenario/<scenario-id>/`. That
  still holds for hand-written scenarios. Instances lifted from real data use `https://w3id.org/sco/data/`.
