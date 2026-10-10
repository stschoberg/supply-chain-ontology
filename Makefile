# Supply Chain Ontology build.
#
# Python targets (test, validate, lint) only need `uv`.
# ROBOT targets (components, reason, report, release) run in Docker unless a working local Java is found
# (as in CI). Force either with ROBOT_ENV=docker or ROBOT_ENV=local. The jar is downloaded on first use.

SHELL := /bin/bash
.DEFAULT_GOAL := help

ROBOT_VERSION := 1.9.11
ROBOT_JAR     := tools/robot.jar
ROBOT_IMAGE   := eclipse-temurin:21-jre
ROBOT_ENV     ?= $(shell java -version >/dev/null 2>&1 && echo local || echo docker)
ifeq ($(ROBOT_ENV),docker)
ROBOT := docker run --rm --user "$$(id -u):$$(id -g)" -v "$(CURDIR)":/work -w /work \
	$(ROBOT_IMAGE) java -jar $(ROBOT_JAR)
else
ROBOT := java -jar $(ROBOT_JAR)
endif

ONT        := ontology
EDIT       := $(ONT)/src/sco-edit.ttl
CATALOG    := $(ONT)/catalog-v001.xml
RELEASE    := $(ONT)/release
VERSION    := $(shell date +%Y-%m-%d)
BASE_IRI   := https://w3id.org/sco
PREFIXES   := --prefix "sco: $(BASE_IRI)/" --prefix "skos: http://www.w3.org/2004/02/skos/core\#"

TEMPLATES  := $(wildcard $(ONT)/src/templates/*.tsv)
COMPONENTS := $(patsubst $(ONT)/src/templates/%.tsv,$(ONT)/components/%.owl,$(TEMPLATES))

.PHONY: help all test validate lint fmt components reason report release refresh-imports refresh-iof clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

all: test reason report ## Everything CI runs

# ---------------------------------------------------------------- Python

test: ## Run the pytest suite
	uv run pytest

validate: ## SHACL-validate all scenarios
	uv run sco validate

lint: ## Lint and format-check Python
	uv run ruff check .
	uv run ruff format --check .

fmt: ## Auto-format Python
	uv run ruff check --fix .
	uv run ruff format .

# ---------------------------------------------------------------- Data

include data/data.mk

# ---------------------------------------------------------------- ROBOT

$(ROBOT_JAR):
	mkdir -p tools
	curl -fsSL -o $@ https://github.com/ontodev/robot/releases/download/v$(ROBOT_VERSION)/robot.jar

components: $(COMPONENTS) ## Regenerate OWL components from ROBOT templates

$(ONT)/components/%.owl: $(ONT)/src/templates/%.tsv | $(ROBOT_JAR)
	$(ROBOT) template --template $< $(PREFIXES) \
		--ontology-iri "$(BASE_IRI)/components/$*.owl" \
		--output $@

reason: $(COMPONENTS) | $(ROBOT_JAR) ## Check consistency and unsatisfiable classes with HermiT (OWL 2 DL)
	mkdir -p $(RELEASE)
	$(ROBOT) merge --catalog $(CATALOG) --input $(EDIT) \
		reason --reasoner HermiT --equivalent-classes-allowed asserted-only --output $(RELEASE)/reasoned.owl

# report-profile.txt omits missing_definition: ROBOT expects IAO:0000115, but we follow BFO 2020
# and CCO in using skos:definition. tests/test_ontology.py checks definitions instead.
report: $(COMPONENTS) | $(ROBOT_JAR) ## Ontology quality report (labels, definitions, ...)
	mkdir -p $(RELEASE)
	$(ROBOT) merge --catalog $(CATALOG) --input $(EDIT) \
		remove --base-iri "$(BASE_IRI)/" --axioms external --preserve-structure false \
		report --profile $(ONT)/report-profile.txt --fail-on ERROR --output $(RELEASE)/report.tsv

release: $(COMPONENTS) | $(ROBOT_JAR) ## Build release artifacts in ontology/release/
	mkdir -p $(RELEASE)
	$(ROBOT) merge --catalog $(CATALOG) --input $(EDIT) \
		reason --reasoner HermiT --equivalent-classes-allowed asserted-only \
		annotate --ontology-iri "$(BASE_IRI)/sco-full.owl" \
		         --version-iri "$(BASE_IRI)/releases/$(VERSION)/sco-full.owl" \
		convert --output $(RELEASE)/sco-full.owl \
		convert --output $(RELEASE)/sco-full.ttl
	@echo "Release artifacts in $(RELEASE)/"

refresh-imports: ## Re-download BFO 2020 core
	curl -fsSL -o $(ONT)/imports/bfo-core.owl http://purl.obolibrary.org/obo/bfo/2020/bfo-core.owl

# ---------------------------------------------------------------- Research

# The IOF release that research/ studies. Findings cite it, so bump it on purpose.
IOF_RELEASE := Release_202603
IOF_DIR     := research/reference/iof-scro
IOF_RAW     := https://raw.githubusercontent.com/iofoundry/ontology/$(IOF_RELEASE)

refresh-iof: ## Re-download the pinned IOF Core + SCRO release into research/reference/
	curl -fsSL -o $(IOF_DIR)/SupplyChain.rdf $(IOF_RAW)/supplychain/SupplyChain.rdf
	curl -fsSL -o $(IOF_DIR)/Core.rdf $(IOF_RAW)/core/Core.rdf
	curl -fsSL -o $(IOF_DIR)/AnnotationVocabulary.rdf $(IOF_RAW)/core/meta/AnnotationVocabulary.rdf
	curl -fsSL -o $(IOF_DIR)/bfo.rdf $(IOF_RAW)/cache/bfo/2020/bfo.rdf
	curl -fsSL -o $(IOF_DIR)/LICENSE $(IOF_RAW)/LICENSE

clean: ## Remove build outputs
	rm -rf $(RELEASE)/*
