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
| `models/staging/<source>/` | views | `stg_<source>__<entity>` | One per raw table: dedupe, rename, type, parse. No joins, no business logic. |
| `models/marts/` | tables | `<entity>` | **Published.** Joined across sources, shaped like the ontology's kinds (organizations, products, awards). Enforced [contracts](https://docs.getdbt.com/docs/collaborate/govern/model-contracts): column names and types are the public interface. Input to `data/mappings/`. |
| `models/meta/` | tables | `meta_<thing>` | **Published.** Provenance: source files with checksums, and the build (tag, git commit). |

Models tagged `published` (everything in `marts/` and `meta/`) are exported to Parquet by `make dist`.
Staging is internal and may change freely. Removing or retyping a published column is a breaking change;
call it out in the release notes.

- **Sources** read snapshot CSVs in place with DuckDB's `read_csv`. The snapshot directory is a dbt var
  (`usaspending_snapshot`), which `make transform` sets to the newest one.
- **Tests:** dbt data tests run against real data in `make transform`. `tests/test_transform.py` builds the
  project against `tests/fixtures/` so CI checks the logic without network.
- `profiles.yml` is committed: no secrets. Set `SCO_WAREHOUSE` to build somewhere else.
- **Locking:** DuckDB allows one process per file when any of them writes. While a CLI or UI session has
  `data/warehouse.duckdb` open, even read-only, `make transform` fails with a lock error. Close the session
  first. `make dist` builds in a temporary database, so it isn't affected.
