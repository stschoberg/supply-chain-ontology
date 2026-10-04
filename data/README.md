# Data

The data engineering half of the project: extract and load real-world sources, transform them with dbt in
DuckDB, and map the results into scenario ABoxes.

```
sources/<source>/fetch.py ──► sources/<source>/raw/ ──► transform/ (dbt) ──► warehouse.duckdb ──► mappings/ ──► scenarios/
        extract + load              snapshots             staging → marts                          → RDF
```

```bash
make fetch-usaspending    # E + L: download a snapshot
make transform            # T: dbt build (models + data tests) into data/warehouse.duckdb
make dist                 # package a release in data/dist/
```

## Data releases

The published data product is a GitHub Release tagged `data-YYYY-MM-DD`. Each release holds:

| Asset | What it is |
|---|---|
| `<table>.parquet` | One file per published model (`awards`, `meta_*`). **The data.** Readable by any tool. |
| `catalog.duckdb` | Views over those Parquet files, so DuckDB users can `attach` and see named tables. Holds no data. |
| `raw-<source>-<snapshot>.tar` | The raw source files the tables were built from, for exact reproduction. |
| `RELEASE_NOTES.md`, `SHA256SUMS` | Provenance, row counts, checksums. |

```sql
attach 'https://github.com/stschoberg/supply-chain-ontology/releases/download/<tag>/catalog.duckdb' as sco;
select * from sco.awards limit 10;
```

Dated releases never change; cite one in written work. Publishing from CI is not set up yet; `make dist`
builds the same files locally.

## Sources

| Source | What it gives us | Angle | Status |
|--------|------------------|-------|--------|
| [USAspending.gov](sources/usaspending/README.md) | Federal contract awards: vendor, product/service code, competition, origin | DoD + civilian | Fetching |
| [SAM.gov](https://sam.gov/) entity data | Vendor registrations, CAGE codes, ownership | DoD | Candidate |
| [USGS Mineral Commodity Summaries](https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries) | Critical minerals: production by country, US import reliance | DoD (industrial base) | Candidate |
| [UN Comtrade](https://comtradeplus.un.org/) | Bilateral trade flows by HS code | Civilian / global | Candidate |
| [BTS Freight Analysis Framework](https://www.bts.gov/faf) | US freight flows by mode, origin, and destination | Civilian logistics | Candidate |
| [IMF PortWatch](https://portwatch.imf.org/) | Port activity and chokepoint disruptions | Disruption scenarios | Candidate |

## Layout

```
data/
  sources/<source>/
    README.md               # license, cadence, access, columns we use, quirks
    fetch.py                # uv run python -m data.sources.<source>.fetch
    raw/<snapshot-date>/    # downloaded files, untouched, + .manifest.json (gitignored)
  transform/                # dbt project: staging → marts (see its README)
  release.py                # packages published models as a release (make dist)
  warehouse.duckdb          # dbt output (gitignored)
  dist/                     # release output (gitignored)
  mappings/                 # marts → RDF, written to scenarios/<name>/
```

## Fetching well

- **Prefer bulk downloads over search APIs.** Search APIs return fewer fields and paginate. Fetch whole
  records and narrow them during staging.
- **Raw files are immutable snapshots.** A refetch goes in a new snapshot directory, never over an old one.
- **Verify what came back:** that the server applied our filters, that row counts match, and that the
  columns we depend on exist. Fail loudly otherwise.
- **Keep API keys in environment variables** (or a gitignored `.env`), never in the repo.
- **Shared plumbing** (retries, User-Agent, OS certificate store, manifests) lives in `src/sco/fetching.py`.
