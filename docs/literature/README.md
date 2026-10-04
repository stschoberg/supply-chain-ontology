# Literature

What we read, and how it bears on the ontology. Notes here are the evidence behind the
[ADRs](../adr/) and [competency questions](../../competency-questions/).

## Workflow

- **Library:** shared [Zotero group library](https://www.zotero.org/groups/6681419/phi-598-supply-chain-ontology) with the Better BibTeX plugin, auto-exporting to `docs/literature/library.bib` (PDFs stay in Zotero, not git).
- **Notes:** one markdown file per paper in `docs/literature/notes/`, named by citekey, copied from `docs/literature/_template.md`.

## Zotero setup

1. Install [Zotero](https://www.zotero.org/download/) and join the group linked above.
2. Install the [Better BibTeX](https://retorque.re/zotero-better-bibtex/installation/) plugin (Tools → Plugins → Install Plugin From File, using the latest `.xpi` from its releases page).
3. In Settings → Better BibTeX → Export → Fields, add `file, abstract, copyright, langid, urldate` to "Fields to omit from export". This keeps local paths out of the repo.
4. Right-click the group library, choose Export, format **Better BibTeX**, check **Keep updated**, and save to `docs/literature/library.bib` in this repo. Don't edit that file by hand. It is the only bibliography file in the repo.
5. Add papers to the group library, then write a note in `docs/literature/notes/` named with the item's citekey (e.g. `mentzerDefiningSupplyChain2001.md`).

> **Moved from `literature/` and `references/`?** Better BibTeX keeps writing to the old path until you change it.
> Remove the old automatic export (Settings → Better BibTeX → Automatic export) and redo step 4 with the new path.

## Linking literature to the ontology

- **`informs:`** in a note's frontmatter lists the IDs the paper bears on: `CQ-002`, `ADR-0001`.
- **Cite papers** in CQ and ADR files by citekey: `[@mentzerDefiningSupplyChain2001]`.
- **`tests/test_literature.py` checks both,** and CI runs it:
  - every note's citekey exists in `library.bib` and matches the note's file name
  - every `informs:` entry names an existing CQ or ADR
  - every `[@citekey]` in a CQ or ADR exists in `library.bib`
