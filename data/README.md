# Data

`raw/` is gitignored. Every source must have a fetch script in `pipelines/` so anyone can reproduce the data. Note
each source's license and update cadence here.

## Candidate sources

| Source | What it gives us | Angle |
|--------|------------------|-------|
| [USAspending.gov](https://www.usaspending.gov/) / FPDS | Federal contract awards: vendor, product/service code, agency | DoD + civilian |
| [SAM.gov](https://sam.gov/) entity data | Vendor registrations, CAGE codes, ownership | DoD |
| [USGS Mineral Commodity Summaries](https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries) | Critical minerals: production by country, US import reliance | DoD (industrial base) |
| [UN Comtrade](https://comtradeplus.un.org/) | Bilateral trade flows by HS code | Civilian / global |
| [BTS Freight Analysis Framework](https://www.bts.gov/faf) | US freight flows by mode, origin, and destination | Civilian logistics |
| [IMF PortWatch](https://portwatch.imf.org/) | Port activity and chokepoint disruptions | Disruption scenarios |

## Layout

- `raw/`: downloaded files, untouched (gitignored)
- `mappings/`: source → RDF mappings (YARRRML/RML, or SPARQL CONSTRUCT)
- Pipeline output goes to `scenarios/<name>/`, not here.
