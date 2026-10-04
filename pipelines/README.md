# Pipelines

ETL that turns real-world data into scenario instance data (ABox). Each pipeline should:

1. **Fetch** raw data into `data/raw/<source>/`, idempotently.
2. **Transform** it into RDF using the shared namespaces in `sco.namespaces` (never hard-coded IRIs).
3. **Write** the result to `scenarios/<scenario>/data.ttl` (or extra `*.ttl` files there; all are loaded).
4. **Pass** `uv run sco validate <scenario>`.

Run pipelines as modules, e.g. `uv run python -m pipelines.usgs_minerals`. Pipeline output should be
deterministic, so diffs show real changes.
