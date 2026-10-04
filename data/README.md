# Data

Real-world instance data for testing the ontology. Today that is one source, **USAspending.gov**: the
Department of Defense's contract awards for bearings, published as-is (typed and deduplicated, nothing
inferred). It is versioned, so a CQ result can name the exact data it ran on.

| | |
|---|---|
| Contents | DoD contract awards for bearings (PSC 3110, 3120, 3130) with any activity in FY2023–FY2025 |
| Size | 38,117 awards, 1,329 suppliers, $877M obligated (release `data-2026-10-04`) |
| Updated | On demand. Each release is a dated, immutable snapshot. |
| License | Public domain (U.S. Government works) |
| Columns | [Data dictionary](DICTIONARY.md) |

## Connect

Everything is in the repo's [GitHub releases](https://github.com/stschoberg/supply-chain-ontology/releases).
There's nothing to install beyond a tool that reads Parquet, and nothing to clone.

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

**Python:**

```python
import duckdb  # pip install duckdb pandas

url = "https://github.com/stschoberg/supply-chain-ontology/releases/download/data-latest"
awards = duckdb.read_parquet(f"{url}/stg_usaspending__awards.parquet").df()  # a pandas DataFrame
```

**Anything else** (R, Excel via Power Query, Spark): download the `.parquet` files from a release.

## Tables

| Table | One row per | |
|---|---|---|
| `stg_usaspending__awards` | Contract award (a contract or order, modifications rolled up) | The data |
| `meta_source_files` | Raw file the release was built from, with its checksum and the API request | Provenance |
| `meta_build` | The release itself: tag, git commit, build time | Provenance |

Names say where data comes from: `stg_<source>__<thing>` is one source's records as published,
cleaned but not reinterpreted. Tables that combine sources or reshape records into the ontology's
kinds will get plain names (`suppliers`, `products`) when they exist.

## What it can and can't tell you

**Can:**

- **Who supplied what kind of product, and for how much:** supplier (`recipient_uei`), corporate
  parent, product class (`psc`), dollars.
- **Whether a purchase was competed:** `extent_competed`, `offers_received` (29% of awards drew a
  single offer), and the legal reason when it wasn't.
- **Where it came from:** `origin_country` and the supplier's ownership (`domestic_or_foreign_entity`).

**Can't (yet):**

- **Which specific part was bought.** Awards name a kind of item (`BEARING,BALL,ANNULAR`), truncated
  and spelled inconsistently. The part-level ID, the NSN, appears in only 221 awards. Questions like
  CQ-002 ("which products are single-sourced?") can only be answered at the product-class level.
  [Details and options](sources/usaspending/README.md#known-gaps).
- **Deliveries.** An award is a commitment to buy, not a record that goods arrived.
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
- **`data-YYYY-MM-DD`** releases never change. Cite one in written work and pin it in anything that
  should be reproducible, e.g. "CQ-002 over `data-2026-10-04`". Swap the tag into the URLs above.
- Each release's notes list its row counts, data dictionary, source snapshots, and git commit, and it
  includes the raw source files for exact reproduction.
- Removing or retyping a column is announced in the release notes.

## Sources

| Source | Status |
|---|---|
| [USAspending.gov](sources/usaspending/README.md): federal contract awards | Published |
| [SAM.gov](https://sam.gov/) entity data: registrations, CAGE codes, ownership | Candidate |
| [USGS Mineral Commodity Summaries](https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries): critical minerals by country | Candidate |
| [UN Comtrade](https://comtradeplus.un.org/): bilateral trade flows by HS code | Candidate |
| [BTS Freight Analysis Framework](https://www.bts.gov/faf): US freight flows | Candidate |
| [IMF PortWatch](https://portwatch.imf.org/): port activity and chokepoint disruptions | Candidate |

---

Building, testing, and publishing the data: [ENGINEERING.md](ENGINEERING.md).
