# Data

The data engineering half of the project: extract real-world sources, process them, and map the results into
scenario ABoxes. Each source has a `fetch.py` so anyone can reproduce the data, and a `README.md` covering its
license, update cadence, access method, the columns we use, and its quirks.

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

```bash
make fetch-usaspending    # download a snapshot
```

```
data/
  sources/<source>/
    README.md               # license, cadence, access, columns we use, quirks
    fetch.py                # uv run python -m data.sources.<source>.fetch
    raw/<snapshot-date>/    # downloaded files, untouched, + .manifest.json (gitignored)
  mappings/                 # processed data → RDF, written to scenarios/<name>/
```

## Fetching well

- **Prefer bulk downloads over search APIs.** Search APIs return fewer fields and paginate. Fetch whole
  records and narrow them during staging.
- **Raw files are immutable snapshots.** A refetch goes in a new snapshot directory, never over an old one.
- **Verify what came back:** that the server applied our filters, that row counts match, and that the
  columns we depend on exist. Fail loudly otherwise.
- **Keep API keys in environment variables** (or a gitignored `.env`), never in the repo.
- **Shared plumbing** (retries, User-Agent, OS certificate store, manifests) lives in `src/sco/fetching.py`.
