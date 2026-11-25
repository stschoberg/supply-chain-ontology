---
citekey: ameriModelingSupplyChain2019
title: Modeling a Supply Chain Reference Ontology Based on a Top-Level Ontology
year: 2019
status: reading
read_by: []
relevance: core
approach: [bfo, supply-chain, methodology]
component: academic
tags: [scro, iof, bfo-evaluation, roles, cco]
informs: [ADR-0001, ADR-0004]
---

## Summary
The paper that introduced the Supply Chain Reference Ontology (SCRO), by Farhad Ameri (now SCRO's maintainer) and
Boonserm Kulvatunyou (NIST), developed within the Industrial Ontologies Foundry (IOF) with BFO as the top level. It
describes how terms were collected and defined, gives draft first-order axioms for agents, supplier and customer
roles, capabilities, and the flow of goods and information, and tests SCRO by extending it into an application
ontology for supplier discovery. One stated aim was to evaluate BFO itself as a top-level ontology for supply chains.

## Key claims
- Existing supply chain ontologies fail at interoperability, partly because they model views of supply chains
  rather than supply chains; a shared, realist top level is offered as the remedy (pp. 1-2).
- BFO was chosen for its user base (including military and intelligence), small size, and documentation, but "does
  not mean that it is necessarily the best"; at the time IOF had not committed to a single top-level ontology and was
  weighing DOLCE, several top levels, or none (p. 3).
- Requirements for SCRO, in RFC 2119 terms (p. 5): every class SHALL be a subclass of a mid- or top-level class;
  SCRO SHALL reuse existing mid- and top-level relations "to the extent possible"; it SHOULD be small, modular, and
  axiomatized enough for interoperability.
- Roles are the main device: supplier, customer, and service provider roles, with defined classes such as supplier
  = agent bearing a supplier role (pp. 6-7). Role axioms carry an explicit time ("has role at t") in the first-order
  versions.
- In this draft, moving goods between suppliers is an **Act of Shipment**, a process (a CCO act of location change)
  in which the goods participate, with one supplier as sender and one as receiver (p. 9).
- SCRO imported CCO for time, units, and geography, plus an IOF proof-of-concept top-level module (p. 3).
- Conclusion on BFO: its breadth is adequate for common supply chain entities and its axioms gave the logical
  consistency the use cases needed; harder interoperability cases still need testing. Its realism makes abstract
  notions, such as supply chain models used for simulation, need workarounds (p. 12).

## Method / data
Use-case-driven: members proposed four use cases (supplier discovery, supply chain configuration, bidding
automation, traceability), each with a problem statement, key terms, and at least five competency questions. About 80
terms were collected and given expert definitions from internal and external sources (Ontobee, ISO, APICS), then
genus-differentia formal definitions and OWL axioms (pp. 3-5). Validation is one use case, supplier discovery:
SCRO's capability module is extended into an application ontology, queried with SPARQL, and used for rule-like
capability inference in a proof-of-concept tool (pp. 10-12). No data set is described.

## What BFO's commitments buy or cost here
- **Buy, by the authors' account:** coverage of the common entities, and consistency. Neither is measured; the
  evaluation criteria (completeness, consistency, accuracy) are named but no results are reported for them (p. 12).
- **Cost:** abstract and non-existent things (models, plans for simulation) need workarounds under BFO's realism
  (p. 12).
- **Roles as engineering, not ontology:** "Role may also be viewed as a work around to maintain a single inheritance
  hierarchy" (p. 6). That bears on attribution: some of SCRO's heavy use of roles may be IOF's design choice, made
  to keep a single-inheritance hierarchy, rather than something BFO forces.

## Relevance to our project
- **Prior answer to our research question.** This is the published claim that BFO is adequate for supply chains,
  made by the people who built the stack we study. Our findings test it, and it explicitly asks for further testing.
- **F-004 (draft):** SCRO's own requirement to reuse top- and mid-level relations can be set against our count: 13
  of SCRO's 18 relations, and 49 of IOF Core's 83, have no BFO parent.
- **F-003 (draft):** the "work around" quote is direct evidence for attributing the role pattern to IOF.
- **[F-001](../../../research/findings/F-001.md):** the 2019 draft named the *process* a shipment ("Act of
  Shipment"); the release we pinned uses "shipment" for the goods and "transport process" for the moving. SCRO
  changed what "shipment" names. Worth asking Ameri why.
- **F-002:** the role axioms are time-indexed only in first-order logic, not in OWL; the same gap F-002 describes.
- **ADR-0001:** SCRO was originally built on CCO; the release we use is built on IOF Core.
- **Traceability:** one of SCRO's four motivating use cases, not validated here; see
  [[ameriEnablingTraceabilityAgriFood2022]], which builds it on SCRO. One network CQ here is already a traceability
  question: "What is the path followed by a certain component in this network?" (p. 10).

## Limitations
- A preprint of a draft ontology; the authors say the axioms are drafts and may be too weak or too strong (p. 6).
- The BFO evaluation is a conclusion without reported evidence.
- Validation covers one use case, by the authors, without real data.
- No comparison against a non-BFO top level, though the paper says one was planned (p. 3).

## Quotes
> "One of the objectives of the current experiment was to evaluate BFO as an upper ontology for the supply-chain
> domain." (p. 12)

> "The results of the evaluation indicated that the breadth of coverage of BFO is adequate to represent commonly used
> entities in the supply chain domain." (p. 12)

> "Workarounds are often needed to address abstract notions in BFO." (p. 12)

> "Role may also be viewed as a work around to maintain a single inheritance hierarchy." (p. 6)

> "SCRO SHALL reuse the existing relationships available in mid-level and top-level ontologies to the extent
> possible." (p. 5)

> "At the time of writing this paper, IOF has not committed to adopting a single top-level ontology yet" (p. 3)

## Open questions
- Why did "shipment" move from the process to the goods between this draft and the current release?
- Was the planned DOLCE comparison ever done?
- When and why did SCRO move from CCO to IOF Core?
