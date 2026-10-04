# Transform (dbt + DuckDB)

Turns raw source snapshots into tidy, tested tables in `data/warehouse.duckdb` (gitignored, rebuilt anytime).

```bash
make transform                         # dbt build: models + data tests, newest snapshot of each source
duckdb -readonly data/warehouse.duckdb # explore with the DuckDB CLI (brew install duckdb)
```

For the browser UI, start it on an in-memory database and attach the warehouse, since `-ui` doesn't work with
`-readonly`: run `duckdb -ui`, then `attach 'data/warehouse.duckdb' as wh (read_only);`.

| Layer | Materialized | Naming | Job |
|---|---|---|---|
| `models/staging/<source>/` | views | `stg_<source>__<entity>` | One per raw table: dedupe, rename, type, parse. No joins, no business logic. A staging model can be **published** as-is, as `stg_usaspending__awards` is. |
| `models/marts/` (none yet) | tables | `<entity>` | Joined across sources and shaped like the ontology's kinds (organizations, products). |
| `models/meta/` | tables | `meta_<thing>` | **Published.** Provenance: source files with checksums, and the build (tag, git commit). |

Models tagged `published` (every `meta_*` model, and any other model tagged in its YAML) are exported to
Parquet by `make dist`. They need enforced [contracts](https://docs.getdbt.com/docs/collaborate/govern/model-contracts)
with a description and type for every column; run `make data-docs` after changing them. Unpublished models
may change freely. See [the published interface](../ENGINEERING.md#the-published-interface).

- **Sources** read snapshot CSVs in place with DuckDB's `read_csv`. The snapshot directory is a dbt var
  (`usaspending_snapshot`), which `make transform` sets to the newest one.
- **Tests:** dbt data tests run against real data in `make transform`. `tests/test_transform.py` builds the
  project against `tests/fixtures/` so CI checks the logic without network.
- `profiles.yml` is committed: no secrets. Set `SCO_WAREHOUSE` to build somewhere else.
- **Locking:** DuckDB allows one process per file when any of them writes. While a CLI or UI session has
  `data/warehouse.duckdb` open, even read-only, `make transform` fails with a lock error. Close the session
  first. `make dist` builds in a temporary database, so it isn't affected.
