# supply-chain-ontology

[PHI 598](https://aowiki.nsm.buffalo.edu/index.php/BFO-Intro-Fall-2026#Course_bibliography) semester project.

Team: Sam Eskew & Sam Schoberg.

Within the supply chain domain, what do BFO's specific categorial commitments buy — or cost — relative to non-BFO approaches to representing the same domain?

## The approach

We build a BFO 2020–aligned supply chain ontology driven by **competency questions** (CQs), questions the
ontology must be able to answer, and test it against two kinds of instance data:

- **Hand-written scenarios:** small, controlled cases where we know the right answer.
- **Real-world data:** U.S. federal procurement records, to see whether the model holds up outside the cases we designed it for.
  Procurement records stop at the contract, so a **synthetic** source invents the logistics that would follow
  each real award, in the shape of the DoD's own transaction standards. It gives the ontology something
  supply-chain-shaped to describe; it is not evidence that real data fits.

Where real data maps cleanly, the ontology earns its keep. Where it doesn't, that's a finding about what
BFO's commitments cost or buy.

## Data workflow

The data is published as dated releases of a few documented tables: DoD contract awards for bearings from
USAspending.gov (FY2023–25), and synthetic logistics records generated for them (`dlms_synth`). How to use it,
and what it can't tell you: [data/README.md](data/README.md).

```bash
make fetch-usaspending           # download a raw snapshot
make transform                   # dbt build + data tests into data/warehouse.duckdb
make dist                        # package a release locally in data/dist/, tables and RDF graph
```

Publishing, adding a source, and the published-table contract: [data/ENGINEERING.md](data/ENGINEERING.md).
Lifting the tables into RDF: [data/mappings/](data/mappings/README.md).

## Ontology workflow

### Quick start

```bash
uv sync                          # Python deps (rdflib, owlrl, pyshacl)
make test                        # CQ tests, SHACL validation, structural checks
uv run sco list                  # list competency questions and scenarios
uv run sco query CQ-002          # run a CQ against a reasoned scenario
```

ROBOT targets (the OWL toolchain) run in Docker, so you don't need to install Java. If a working local Java is
found, as in CI, it's used instead.

```bash
make reason                      # OWL 2 DL consistency check with HermiT
make report                      # ontology quality report
make release                     # build ontology/release/
make help                        # all targets
```

### Adding to the ontology

1. **Add a competency question:** write `competency-questions/CQ-NNN.md` and `CQ-NNN.rq`.
2. **Extend the ontology** to support it: `sco-edit.ttl` or a template. Every class needs a label and a
   `skos:definition`, and must be rooted in BFO.
3. **Add or extend a scenario,** with expected results in `scenarios/<name>/expected/CQ-NNN.csv`.
4. `make test && make reason` should pass. CI enforces both on every PR.
5. **Record non-obvious modeling choices** as an ADR in `docs/adr/`.

### How the pieces fit

```
  competency question ──► SPARQL query (.rq) ──┐
                                               ▼
  TBox (sco-edit + imports) ─┐            ┌─ query results ──► compare to scenarios/*/expected/*.csv
                             ├─► reason ──┤
  scenario ABox (data.ttl) ──┘            └─ SHACL validate ──► data-quality report
```

- **OWL reasoning** (open world) classifies things and infers facts, e.g. an organization bearing a supplier role
  *is* a supplier.
- **SHACL** (closed world) checks that data is complete, e.g. a supply process with no product is an error.
- **SPARQL** answers the CQs over the reasoned graph, including closed-world questions like "exactly one supplier".

Tests use OWL 2 RL (pure Python, fast). `make reason` runs full OWL 2 DL with HermiT over the TBox.

### Conventions

- Namespace: `https://w3id.org/sco/` (prefix `sco:`). Not yet registered with w3id; see [ADR-0003](docs/adr/0003-iri-scheme.md).
- BFO terms are referenced by their OBO IRIs (`obo:BFO_0000196`), with the label in a trailing comment.
- Classes are UpperCamelCase, properties lowerCamelCase, and labels are lowercase English.
- Definitions use the genus–differentia form: "A *[parent]* that *[distinguishing features]*."

## Research workflow

The research workflow uses the other two to answer the project question. It traces BFO's influence down
through a published BFO-based supply chain stack (IOF Core and its Supply Chain Reference Ontology), and through our
own ontology, to instance data. Each result is recorded as a finding that says which layer caused it: BFO, IOF, or
us.

- **Read the analysis:** [How BFO shapes IOF Core and SCRO](https://stschoberg.github.io/supply-chain-ontology/),
  rebuilt from `research/notebooks/` on every push to `main`.
- **Method, findings, and plan:** [research/README.md](research/README.md).

## Layout

| Path | What lives there |
|------|------------------|
| `ontology/src/sco-edit.ttl` | **The ontology (TBox).** Edit this in Protégé or a text editor. |
| `ontology/src/templates/*.tsv` | Spreadsheet-maintained classes ([ROBOT templates](https://robot.obolibrary.org/template)). Run `make components` after editing. |
| `ontology/components/` | OWL generated from templates. Committed so Python tooling works without Java. |
| `ontology/imports/` | External ontologies (BFO 2020 core; CCO or IOF once [ADR-0001](docs/adr/0001-mid-level-ontology.md) is decided). |
| `ontology/catalog-v001.xml` | Maps import IRIs to local files, for Protégé and ROBOT. |
| `ontology/release/` | Build outputs (`make release`). Gitignored; CI uploads them as artifacts. |
| `competency-questions/` | `CQ-NNN.md` (the question and its rationale) + `CQ-NNN.rq` (the SPARQL that answers it). |
| `scenarios/<name>/` | Instance data (ABox) for one scenario: `data.ttl`, a narrative `README.md`, and `expected/CQ-NNN.csv`. |
| `shapes/` | SHACL shapes: closed-world data-quality checks. |
| `data/` | The data product ([README](data/README.md)) and the pipeline that builds it ([ENGINEERING](data/ENGINEERING.md)). |
| `src/sco/` | Shared Python: graph loading, reasoning, CLI, and `sco.iof_stack` (the research tables as DataFrames). |
| `tests/` | pytest suite. |
| `docs/adr/` | Architecture/modeling decision records. |
| `research/` | Method, findings, notebooks, and pinned reference ontologies for the project question. See [its README](research/README.md). |
| `docs/literature/` | Bibliography (Zotero export) and per-paper notes, linked to CQs and ADRs. See [its README](docs/literature/README.md). |
