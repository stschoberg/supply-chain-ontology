# Data

Instance data for testing the ontology, from two sources:

- **USAspending.gov** (real): the Department of Defense's contract awards for bearings, published as-is (typed
  and deduplicated, nothing inferred).
- **`dlms_synth`** (synthetic): invented DoD logistics records, such as shipments, receipts, and requisitions,
  generated for those awards, because USAspending stops at the contract. Marked synthetic everywhere.

It is versioned, so a CQ result can name the exact data it ran on. The table below describes the real data.

| | |
|---|---|
| Contents | DoD contract awards for bearings (PSC 3110, 3120, 3130) with any activity in FY2023–FY2025 |
| Size | 38,117 awards, 1,329 suppliers, $877M obligated (release `data-2026-10-04`) |
| Updated | On demand. Each release is a dated, immutable snapshot. |
| License | Public domain (U.S. Government works) |
| Columns | [Data dictionary](DICTIONARY.md) |

## Connect

Everything is in the repo's [GitHub releases](https://github.com/stschoberg/supply-chain-ontology/releases),
as Parquet and CSV. Nothing to clone. Pick whichever fits:

**No install: the example notebook.**
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/stschoberg/supply-chain-ontology/blob/main/data/examples/explore.ipynb)
It runs in Google Colab with example questions: top suppliers, product classes, single-sourcing
(toward CQ-002), and countries of origin. Source: [examples/explore.ipynb](examples/explore.ipynb).

**Spreadsheets** (Excel, Google Sheets, Numbers): download
[`stg_usaspending__awards.csv`](https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest/stg_usaspending__awards.csv)
(about 16 MB) and open it.

**DuckDB** ([install](https://duckdb.org/docs/installation/); `duckdb -ui` opens it in the browser):

```sql
attach 'https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest/catalog.duckdb' as sco;

show tables from sco;
select * from sco.stg_usaspending__awards limit 10;

-- the data dictionary, from inside DuckDB
select column_name, data_type, comment from duckdb_columns()
where database_name = 'sco' and table_name = 'stg_usaspending__awards';
```

The catalog holds no data. Queries read only what they need from the release's Parquet files.

**Python** (pandas or polars):

```python
import pandas as pd  # pip install pandas pyarrow (or: import polars as pl; pl.read_parquet)

url = "https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest"
awards = pd.read_parquet(f"{url}/stg_usaspending__awards.parquet")
```

**R:**

```r
url <- "https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest"
awards <- read.csv(paste0(url, "/stg_usaspending__awards.csv"))

# or Parquet, which keeps column types: download it, then read it with arrow
download.file(paste0(url, "/stg_usaspending__awards.parquet"), "awards.parquet", mode = "wb")
awards <- arrow::read_parquet("awards.parquet")
```

**RDF** (rdflib, Oxigraph, or any triple store): each release also has the same rows as graphs.
Every graph is a pair of files: `<name>.nt.gz` (gzipped N-Triples) is the one to load, holding the
schema and all the data, and `<name>.schema.ttl` is the schema alone, for reading or for Protégé.

| Graph | What it is |
|---|---|
| [`usaspending.nt.gz`](https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest/usaspending.nt.gz) | What the tables say, in USAspending's own terms: an award is a node with one property per column, and its recipient and parent are links to entity nodes. |
| [`dlms_synth.nt.gz`](https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest/dlms_synth.nt.gz) | **Synthetic.** The invented logistics records, in the terms of the DoD transactions they are shaped on. Its nodes are under `…/data/synthetic/` and point at the real awards they were generated for. |
| [`iof-scro.experimental.nt.gz`](https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest/iof-scro.experimental.nt.gz) | The same awards in the terms of the [IOF](https://github.com/iofoundry/ontology) supply chain ontologies, with those ontologies included. **Experimental:** the [mapping](mappings/usaspending/iof-scro/README.md) covers who bought from whom and for how much, but not yet what was bought or whether it was competed, and it will change between releases. |

```python
import gzip, urllib.request
from rdflib import Graph  # pip install rdflib

url = "https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest"
data = gzip.decompress(urllib.request.urlopen(f"{url}/usaspending.nt.gz").read())
g = Graph().parse(data=data, format="nt")  # about 800,000 triples; takes a few seconds
```

- **The graphs describe the same nodes.** An award has the same identifier in both, so loading both
  gives each award its USAspending properties and its IOF ones.
- **The IOF graph states facts only.** It says a recipient has a supplier role; that it is therefore
  a *supplier* is for a reasoner to infer.
- **Neither is mapped into the Supply Chain Ontology yet.**

## Tables

| Table | One row per | |
|---|---|---|
| `stg_usaspending__awards` | Contract award (a contract or order, modifications rolled up) | The data |
| `entities` | Organization identified by a UEI: an award's recipient or its corporate parent | Lookup for `recipient_uei` and `recipient_parent_uei` |
| `dlms_synth__*` (nine tables) | **Synthetic.** An invented DoD logistics record: a shipment notice, receipt, acceptance, requisition, issue, and so on | Made-up data shaped like a supply chain. [What is real and what isn't](sources/dlms_synth/README.md) |
| `meta_source_files` | Raw file the release was built from, with its checksum and the API request | Provenance |
| `meta_build` | The release itself: tag, git commit, build time | Provenance |

**Nothing in a `dlms_synth__` table happened.** USAspending has no shipments, so these tables invent what would
follow each real award, in the shape of the DoD's own logistics transactions. They exist to give the ontology
something supply-chain-shaped to describe. Every row has `synthetic = true`. Don't draw conclusions about real
suppliers from them.

Names say where data comes from: `stg_<source>__<thing>` is one source's records as published,
cleaned but not reinterpreted. Tables that combine sources or reshape records into the ontology's
kinds will get plain names (`suppliers`, `products`) when they exist.

## What it can and can't tell you

**Can:**

- **Who supplied what kind of product, and for how much:** supplier (`recipient_uei`), corporate
  parent, product class (`psc`), dollars.
- **Whether a purchase was competed:** `extent_competed`, `offers_received` (42% of awards
  that report it drew a single offer), and the legal reason when it wasn't.
- **Where it came from:** `origin_country`, `place_of_manufacture`, and the supplier's ownership
  (`domestic_or_foreign_entity`).
- **Where the supplier is and where the work is done:** `recipient_city` through `recipient_country`, and
  `place_of_performance_city` through `place_of_performance_country`.
- **When it was meant to happen:** `solicitation_date`, `base_action_date`, and the contracted window,
  `performance_start_date` to `performance_end_date`.
- **Whether the supplier makes the goods:** `recipient_is_manufacturer`.

**Can't (yet):**

- **Which specific part was bought.** Awards name a kind of item (`BEARING,BALL,ANNULAR`), truncated
  and spelled inconsistently. The part-level ID, the NSN, appears in only 221 awards. Questions like
  CQ-002 ("which products are single-sourced?") can only be answered at the product-class level.
  [Details and options](sources/usaspending/README.md#known-gaps).
- **Deliveries.** An award is a commitment to buy, not a record that goods arrived. The performance dates are
  the contracted window, and the place of performance is where the work is done, not where goods were delivered.
- **Sub-tier suppliers.** Who DoD's suppliers buy from is almost never reported (58 subawards).
- **The latest three months.** DoD publishes procurement data with a 90-day delay.

**Watch out for:**

- **Identify suppliers by `recipient_uei`, not by name.** Names vary across awards.
- **Recipients aren't always manufacturers.** Some are distributors or agents, e.g. Canadian
  Commercial Corporation contracts on behalf of Canadian firms.
- **Awards are included for activity in FY2023–25, not for starting then.** `base_action_date` goes back
  to 2008 for long-running contracts.

## Versions and citing

- **`data-latest`** always serves the newest release. Use it for exploring.
- **`data-YYYY-MM-DD`** releases never change (a second one the same day is `data-YYYY-MM-DD.2`).
  Cite one in written work and pin it in anything that should be reproducible, e.g. "CQ-002 over
  `data-2026-10-04`". Swap the tag into the URLs above.
- Each release's notes list its row counts, data dictionary, source snapshots, and git commit, and it
  includes the raw source files for exact reproduction.
- Removing or retyping a column is announced in the release notes.

## Sources

| Source | Status |
|---|---|
| [USAspending.gov](sources/usaspending/README.md): federal contract awards | Published |
| [`dlms_synth`](sources/dlms_synth/README.md): **synthetic** DoD logistics records (shipments, receipts, requisitions) invented for real awards | Published, marked synthetic |

---

Building, testing, and publishing the data: [ENGINEERING.md](ENGINEERING.md).
