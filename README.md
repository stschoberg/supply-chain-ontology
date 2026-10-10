# supply-chain-ontology

[PHI 598](https://aowiki.nsm.buffalo.edu/index.php/BFO-Intro-Fall-2026#Course_bibliography) semester project.

Team: Sam Eskew & Sam Schoberg.

Within the supply chain domain, what do BFO's specific categorial commitments buy — or cost — relative to non-BFO approaches to representing the same domain?

## The approach

We build a BFO 2020–aligned supply chain ontology driven by **competency questions** (CQs), questions the
ontology must be able to answer, and test it against two kinds of instance data:

- **Hand-written scenarios:** small, controlled cases where we know the right answer.
- **Real-world data:** U.S. federal procurement records, to see whether the model holds up outside the cases we designed it for.

Where real data maps cleanly, the ontology earns its keep. Where it doesn't, that's a finding about what
BFO's commitments cost or buy.

```
  real-world sources ──► data product ──► mappings ──► scenario ABox (RDF) ──┐
                         (versioned tables)                                  ├─► reason, validate, query ──► CQ answers
  competency questions ──► ontology (TBox, BFO-aligned) ─────────────────────┘
```

Two workflows meet at the scenarios: the **data workflow** supplies instances, and the **ontology
workflow** supplies the model and the questions.

## Data workflow

### Using the data

The data is published as a **data product**: a few documented, versioned tables. Ingesting and cleaning
stay hidden behind it. Today it holds DoD contract awards for bearings from USAspending.gov (FY2023–25).

- **No install:** [open the example notebook in Colab](https://colab.research.google.com/github/stschoberg/supply-chain-ontology/blob/main/data/examples/explore.ipynb).
- **DuckDB:**

  ```sql
  attach 'https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest/catalog.duckdb' as sco;
  select * from sco.stg_usaspending__awards limit 10;
  ```

- **What's in it, what it can't tell you, other tools, and how to cite a version:** [data/README.md](data/README.md).
  Every column: [data/DICTIONARY.md](data/DICTIONARY.md).

### Building the data

Each source has a fetcher that saves immutable raw snapshots. dbt transforms them in DuckDB, and a GitHub
Actions workflow publishes the result as a dated release (`data-YYYY-MM-DD`).

```bash
make fetch-usaspending           # download a raw snapshot
make transform                   # dbt build + data tests into data/warehouse.duckdb
make dist                        # package a release locally in data/dist/
```

Publishing, adding a source, and the published-table contract: [data/ENGINEERING.md](data/ENGINEERING.md).
Mappings from the published tables into scenario ABoxes go in [data/mappings/](data/mappings/README.md)
(not started).

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

### Literature

We keep a shared [Zotero group library](https://www.zotero.org/groups/6681419/phi-598-supply-chain-ontology) that
auto-exports to `docs/literature/library.bib`, with one note per paper in `docs/literature/notes/`. Setup and
conventions: [docs/literature/README.md](docs/literature/README.md).

## Research workflow

The research workflow uses the other two to answer the project question. It traces BFO's influence down
through a published BFO-based supply chain stack (IOF Core and its Supply Chain Reference Ontology), and through our
own ontology, to instance data. Each result is recorded as a finding that says which layer caused it: BFO, IOF, or
us.

- **Method:** [research/README.md](research/README.md): the argument, how findings are attributed, metrics, and the
  principles in scope.
- **Findings:** `research/findings/F-NNN.md`, one per result, copied from `research/findings/_template.md`.
- **Reference ontologies:** a pinned IOF release in `research/reference/iof-scro/`. `make refresh-iof` updates it.

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
| `src/sco/` | Shared Python: graph loading, reasoning, CLI. |
| `tests/` | pytest suite. |
| `docs/adr/` | Architecture/modeling decision records. |
| `research/` | Method, findings, notebooks, and pinned reference ontologies for the project question. See [its README](research/README.md). |
| `docs/literature/` | Bibliography (Zotero export) and per-paper notes, linked to CQs and ADRs. See [its README](docs/literature/README.md). |
