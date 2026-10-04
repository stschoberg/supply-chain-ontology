# Data targets: fetch sources, transform with dbt, package releases. Included by the root Makefile,
# so run them from the repo root (`make transform`); paths are relative to it.

.PHONY: fetch-usaspending transform dist data-docs

# Newest snapshot of each source, as an absolute path so warehouse views work from any directory.
# Override with e.g. `make transform USASPENDING_SNAPSHOT=$PWD/data/sources/usaspending/raw/2026-10-04`.
USASPENDING_SNAPSHOT ?= $(abspath $(lastword $(sort $(wildcard data/sources/usaspending/raw/20*))))
DBT := uv run dbt
DBT_FLAGS := --project-dir data/transform --profiles-dir data/transform \
	--vars '{usaspending_snapshot: $(USASPENDING_SNAPSHOT)}'

fetch-usaspending: ## Download DoD bearing awards (PSC 31, FY2023-25) to data/sources/usaspending/raw/
	uv run python -m data.sources.usaspending.fetch

transform: ## Build data/warehouse.duckdb from the newest snapshots with dbt, and run its tests
	@test -n "$(USASPENDING_SNAPSHOT)" || { echo "No USAspending snapshot; run 'make fetch-usaspending'"; exit 1; }
	$(DBT) build $(DBT_FLAGS)

dist: ## Build a data release in data/dist/: Parquet tables, DuckDB catalog, raw archive, notes
	uv run python -m data.release build

data-docs: ## Regenerate data/DICTIONARY.md from the published models' YAML
	uv run python -m data.dictionary
