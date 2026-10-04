# CLAUDE.md

BFO 2020–aligned supply chain ontology. See README.md for layout and workflow.

## Commands

- `make test`: pytest (CQ tests, SHACL, structural checks). Must pass.
- `make reason`: HermiT consistency check. ROBOT runs in Docker when there's no local Java.
- `make components`: regenerate after editing `ontology/src/templates/*.tsv`. Commit the output.
- `uv run sco query CQ-NNN -s <scenario>`: run one CQ.

## Rules

- Every `sco:` class needs `rdfs:label`, `skos:definition` (genus–differentia), and a path to a BFO class.
- Reference BFO by OBO IRI with a label comment: `obo:BFO_0000196  # bearer of`. Verify IRIs against
  `ontology/imports/bfo-core.owl`; don't guess them.
- Never assert membership in a defined class (e.g. `sco:Supplier`); the reasoner infers it.
- Keep TBox (`ontology/`) and ABox (`scenarios/`) separate.
- Record modeling decisions in `docs/adr/`. Don't silently resolve an open ADR.
- `literature/library.bib` is a Zotero auto-export; never edit it by hand. Paper notes go in
  `literature/notes/<citekey>.md`, copied from `literature/_template.md`.
