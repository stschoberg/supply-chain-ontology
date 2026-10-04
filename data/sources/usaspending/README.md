# USAspending.gov

Federal contract awards, derived from FPDS. Used here for DoD purchases of bearings: who supplied what,
whether it was competed, and where it came from.

| | |
|---|---|
| Publisher | U.S. Department of the Treasury, [USAspending.gov](https://www.usaspending.gov/) |
| License | Public domain (U.S. Government work, 17 U.S.C. 105) |
| Access | [API](https://api.usaspending.gov/docs/endpoints), no key needed |
| Updated | Daily. DoD procurement data is published with a 90-day delay, so recent months are incomplete. |
| Fetch | `make fetch-usaspending` ([`fetch.py`](fetch.py)) |
| Raw files | `raw/<snapshot-date>/dod-psc31-fy<FY>.zip` + `.manifest.json`, CSVs extracted to `dod-psc31-fy<FY>/` (gitignored) |
| Staging model | [`stg_usaspending__awards`](../../transform/models/staging/usaspending/stg_usaspending__awards.sql) |

## What we pull

- **Awarding agency:** Department of Defense, which in practice is mostly the Defense Logistics Agency.
- **Products:** PSC group 31, bearings. PSC (Product and Service Code) classifies *what* was bought:
  - `3110` antifriction, unmounted
  - `3120` plain, unmounted
  - `3130` mounted
- **Contract types:** A–D (BPA calls, purchase orders, delivery orders, definitive contracts).
- **Window:** FY2023–FY2025, one file per fiscal year (Oct 1 – Sep 30).
- **Unit:** award summaries, one row per contract or order with its modifications rolled up, plus the
  sparse subaward file.

Each zip holds `Contracts_PrimeAwardSummaries_*.csv` (286 columns) and `Contracts_Subawards_*.csv`. The
manifest records:

- the exact request and the server's echo of it,
- the retrieval time,
- the sha256 of the zip,
- row and column counts per CSV.

## Columns that matter for us

| Column | Use |
|---|---|
| `contract_award_unique_key` | Stable award ID; dedupe on it across fiscal-year files |
| `recipient_uei`, `recipient_name` | The supplier (UEI is SAM.gov's entity ID) |
| `recipient_parent_uei`, `recipient_parent_name` | Corporate parent |
| `cage_code` | Links to SAM.gov / DLA CAGE |
| `product_or_service_code` | PSC class (3110 / 3120 / 3130) |
| `prime_award_base_transaction_description` | Free text: item name, rarely an NSN. See [Known gaps](#known-gaps) |
| `extent_competed`, `number_of_offers_received`, `other_than_full_and_open_competition` | Sole-source signals |
| `country_of_product_or_service_origin`, `domestic_or_foreign_entity` | Foreign dependence |

`fetch.py` fails if any of these columns disappears (`REQUIRED_COLUMNS`).

## Known gaps

### Item identity: which part was bought?

USAspending mostly doesn't say which specific item an award was for.

| In the 2026-10-04 snapshot (38,117 awards) | |
|---|---|
| Descriptions shaped `<10 digits>!<item name>`, e.g. `8510008998!BEARING,BALL,ANNULA` | ~98% |
| Awards with an NSN anywhere in the description | 221 (0.6%) |
| Distinct item-name strings | ~1,270 |

- **The 10-digit number isn't an item ID.** It's unique to each award (37,364 numbers for 37,364 awards), so
  it's likely DLA's purchase request number. It can't link two purchases of the same part.
- **Item names are truncated and spelled inconsistently** (`BEARING,BALL,ANNULA`, `BEARING,BALL,ANNULAR`,
  `BEARING, BALL, ANNULAR`). They name a *kind* of item, not a specific part.
- **The NSN** (National Stock Number: 4-digit supply class + 9-digit item number) is the part-level ID, but it
  appears only in free text and in under 1% of awards. FPDS has no NSN field.

What we *can* identify reliably: the supplier (`recipient_uei`), the award, and the 4-digit product class
(`product_or_service_code`).

**Impact.** Part-level questions like CQ-002 (single-sourced products) can't be answered from USAspending
alone. "Single-sourced" at the PSC or item-name level is answerable but coarse: a class like 3110 covers
thousands of parts with different supply bases.

**Options** (undecided):

1. Answer at the PSC or normalized item-name level, and say so in the CQ.
2. Add a source that lists approved suppliers per NSN, such as DLA's catalog data (FLIS / PUB LOG) or its bid
   board (DIBBS). Access and terms not yet checked.
3. Report the gap itself as a finding. Procurement records leave the item ambiguous between a *kind* of
   part, a catalog entry *about* that kind, and the physical units delivered. BFO keeps those three apart
   (universal, information content entity, material entity), and a flat award schema can't.

### Supply tiers

Subcontract reporting is sparse: 58 subawards across FY2023–25, against 38,117 prime awards. USAspending shows
who DoD buys from, almost never who *they* buy from.

## Gotchas

- **Use `/api/v2/download/awards`, not `/api/v2/bulk_download/awards`.** The bulk endpoint has no PSC filter.
  It accepts one, ignores it without warning, and exports every DoD contract. The fetcher compares the
  server's echoed filters with the ones it sent and stops on any difference.
- **Downloads are async:** submit, poll `/api/v2/download/status`, then fetch the zip. Filtered pulls take
  about a minute per fiscal year.
- **Fiscal-year files overlap.** The time filter matches awards with *any* action in the window, so a
  multi-year contract appears in more than one file.
- **The search API (`/search/spending_by_award`) returns about 10 fields.** The competition and origin
  columns above come only from downloads.
- **When NSNs do appear, the formats vary:** `NSN: 3110-01-526-4555`, `3120001305324 BEARING,SLEEVE`,
  `NSN: 3120015096267LE`. Don't match document numbers like `N4215830672984`.
- **Recipient names vary** (`JAMAICA BEARINGS CO., INC.` vs `JAMAICA BEARINGS CO. INC.`). Use `recipient_uei`.
- **Recipients aren't always manufacturers.** E.g. Canadian Commercial Corporation is a Canadian government
  agency that contracts on behalf of Canadian firms.
- **Data gets restated.** A re-fetch of the same fiscal year can differ, so cite the snapshot date and sha256
  from the manifest.
