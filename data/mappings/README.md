# Mappings

The last step: turn processed source data into scenario instance data (ABox). Each mapping should:

1. **Read** processed data for its sources (see [data/README.md](../README.md)).
2. **Transform** it into RDF using the shared namespaces in `sco.namespaces` (never hard-coded IRIs).
3. **Write** the result to `scenarios/<scenario>/data.ttl` (or extra `*.ttl` files there; all are loaded).
4. **Pass** `uv run sco validate <scenario>`.

Output should be deterministic, so diffs show real changes. Not started; whether mappings are Python
(rdflib) or declarative (SPARQL CONSTRUCT / RML) is open.
