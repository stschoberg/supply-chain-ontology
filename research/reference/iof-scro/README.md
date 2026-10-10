# IOF Supply Chain Reference Ontology (SCRO), pinned

A read-only snapshot of the [Industrial Ontologies Foundry](https://github.com/iofoundry/ontology) supply chain
stack.

| File | What it is | Ontology IRI / version IRI |
|------|------------|----------------------------|
| `SupplyChain.rdf` | SCRO, the supply chain domain layer | `https://spec.industrialontologies.org/ontology/202603/supplychain/SupplyChain/` |
| `Core.rdf` | IOF Core, the mid-level layer SCRO imports | `https://spec.industrialontologies.org/ontology/202603/core/Core/` |
| `AnnotationVocabulary.rdf` | IOF's annotation properties (including the first-order logic annotations), imported by Core | `https://spec.industrialontologies.org/ontology/202603/core/meta/AnnotationVocabulary/` |
| `bfo.rdf` | BFO 2020 as IOF Core imports it: `bfo.owl`, *not* the `bfo-core.owl` in `ontology/imports/` | `http://purl.obolibrary.org/obo/bfo/2020/bfo.owl` |
| `catalog-v001.xml` | Resolves the import chain to these files, for Protégé and ROBOT | |
| `LICENSE` | IOF's MIT license, which covers these files | |

- **Source:** `github.com/iofoundry/ontology`, tag `Release_202603` (published 2026-09-03). `bfo.rdf` is IOF's
  cached copy from `cache/bfo/2020/` in the same tag.
- **Refresh:** `make refresh-iof` re-downloads the tag set by `IOF_RELEASE` in the Makefile. Bump it on purpose, and
  re-run the notebooks: findings cite this release.
- **Open in Protégé:** open `SupplyChain.rdf`. The catalog keeps Protégé off the network.

The two BFO files differ. Both use the same IRIs, but `bfo.rdf` labels the relations with their time
quantifier ("participates in at some time") and adds 24 "at all times" relations that `bfo-core.owl` lacks. See
[F-002](../../findings/F-002.md).
