# Supply Chain Ontology build.
#
# ROBOT targets (reason, report, release) run in Docker unless a working local Java is found
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

.PHONY: help all reason report release refresh-imports clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

all: reason report ## Everything CI runs

# ---------------------------------------------------------------- ROBOT

$(ROBOT_JAR):
	mkdir -p tools
	curl -fsSL -o $@ https://github.com/ontodev/robot/releases/download/v$(ROBOT_VERSION)/robot.jar

reason: | $(ROBOT_JAR) ## Check consistency and unsatisfiable classes with HermiT (OWL 2 DL)
	mkdir -p $(RELEASE)
	$(ROBOT) merge --catalog $(CATALOG) --input $(EDIT) \
		reason --reasoner HermiT --equivalent-classes-allowed asserted-only --output $(RELEASE)/reasoned.owl

# report-profile.txt omits missing_definition: ROBOT expects IAO:0000115, but we follow BFO 2020
# and CCO in using skos:definition.
report: | $(ROBOT_JAR) ## Ontology quality report (labels, definitions, ...)
	mkdir -p $(RELEASE)
	$(ROBOT) merge --catalog $(CATALOG) --input $(EDIT) \
		remove --base-iri "$(BASE_IRI)/" --axioms external --preserve-structure false \
		report --profile $(ONT)/report-profile.txt --fail-on ERROR --output $(RELEASE)/report.tsv

release: | $(ROBOT_JAR) ## Build release artifacts in ontology/release/
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

clean: ## Remove build outputs
	rm -rf $(RELEASE)/*
