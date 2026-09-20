# supply-chain-ontology

[PHI 598](https://aowiki.nsm.buffalo.edu/index.php/BFO-Intro-Fall-2026#Course_bibliography) semester project. 

Team: Sam Eskew & Sam Sam Schoberg.

Within the supply chain domain, what do BFO's specific categorial commitments buy — or cost — relative to non-BFO approaches to representing the same domain?

## Literature workflow

- **Library:** shared [Zotero group library](https://www.zotero.org/groups/6681419/phi-598-supply-chain-ontology) with the Better BibTeX plugin, auto-exporting to `literature/library.bib` (PDFs stay in Zotero, not git).
- **Notes:** one markdown file per paper in `literature/notes/`, named by citekey, copied from `literature/_template.md`.

### Zotero setup

1. Install [Zotero](https://www.zotero.org/download/) and join the group linked above.
2. Install the [Better BibTeX](https://retorque.re/zotero-better-bibtex/installation/) plugin (Tools → Plugins → Install Plugin From File, using the latest `.xpi` from its releases page).
3. In Settings → Better BibTeX → Export → Fields, add `file, abstract, copyright, langid, urldate` to "Fields to omit from export". This keeps local paths out of the repo.
4. Right-click the group library, choose Export, format **Better BibTeX**, check **Keep updated**, and save to `literature/library.bib` in this repo. Don't edit that file by hand.
5. Add papers to the group library, then write a note in `literature/notes/` named with the item's citekey (e.g. `mentzerDefiningSupplyChain2001.md`).
