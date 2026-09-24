---
citekey: morrowDevelopingBasicFormal2021
title: Developing a Basic Formal Supply Chain Ontology to Improve Communication and Interoperability
year: 2021
status: reading
read_by: []
relevance: core
approach: [non-bfo, supply-chain, methodology]
component: academic
tags: [supply-chain, scor, owl, interoperability, dissertation]
informs: []
---


## Summary
An Air Force Institute of Technology dissertation arguing that supply chain management lacks a common language, which makes information exchange between partners difficult, especially as supply chains digitize. Evaluates candidate supply chain frameworks against ontology-design criteria, selects the SCOR (Supply Chain Operations Reference) model version 12.0 as the best starting point, and builds it into a machine-readable OWL ontology in Protégé. Demonstrates it by mapping U.S. Air Force supply chain metrics onto standard SCOR metrics.

## IMPORTANT: this is not actually built on BFO
Despite the title, the delivered ontology is **not** aligned to Barry Smith's Basic Formal Ontology. "Basic formal ontology" in the title and body is used as a generic phrase for a rigorously-defined, machine-readable ontology, not a reference to BFO's upper-level class hierarchy (Continuant, Occurrent, etc.). Arp, Smith & Spear's *Building Ontologies with Basic Formal Ontology* is cited only for its methodological principles (realism, perspectivism, fallibilism, adequatism, p. 44) used to score candidate frameworks, not to import BFO itself. A full-text search found no BFO classes, no "upper ontology" or "top-level ontology" framing, and no BFO import in the actual model. This is a genuine non-BFO approach to the same problem, and a citation trap if skimmed by title alone.

## Key claims
- SCM lacks a common language, and this makes information exchange between partners difficult; a standard language improves interoperability, lowers switching costs between partners, and reduces stock-outs and excess inventory from misinterpretation (pp. vi, 33-34).
- Best practices for ontology development: include domain experts (citing a case where a European financial ontology built without them was "unusable"), use mind maps to capture structure first, and use an open, widely-used tool (OWL) to encode it (pp. 34-35).
- Evaluated four candidate frameworks: APQC Process Classification Framework, the Global Supply Chain Forum model, SCOR, and UN/CEFACT (pp. 38-45).
- Selected SCOR 12.0 as the best starting point, scored against realism, perspectivism, fallibilism, and adequatism (criteria drawn from Arp et al., p. 44); SCOR, APQC, and the Global Supply Chain Forum model represented the domain well, UN/CEFACT only covered international trade specifically (pp. 45-46).
- Built the SCOR 12.0 process/metrics/practices/skills structure into an OWL ontology in Protégé (Chapter IV).
- Demonstrated it by mapping Air Force Sustainment Center metrics (e.g. contract lead time, current inventory) onto standard SCOR metrics, enabling a shared definition across the Air Force and strategic suppliers (GE, Pratt & Whitney, Lockheed Martin, Boeing) (pp. 91-93).
- Author's own limitations: SCOR focuses on operations, not strategy; procurement/acquisition is only "fragmented[ly]" covered in SCOR 12.0; a full logical data model was a goal from the outset but was out of scope (pp. 88-90).

## Method / data
Design science research methodology: literature review and framework comparison, then ontology construction (SCOR 12.0 to OWL/XML via Protégé), demonstrated with an illustrative mapping of real Air Force metrics rather than a full empirical validation. No live multi-firm deployment; recommends testing the resulting ontology in an actual, or at least a more thorough, supply chain environment as future work (p. 92).

## Relevance to our project
This is the closest thing so far in our reading to a real prior attempt at exactly our research question's non-BFO side: a formal, machine-readable supply chain ontology built for cross-firm interoperability, without an upper ontology. Useful as a direct comparison case: what a leader-firm-driven shared vocabulary buys without BFO (the Air Force-to-SCOR-to-supplier metric mapping is close to the leader-firm scenario from [[mentzerDefiningSupplyChain2001]]), versus what BFO's categorial commitments would add or cost on the same problem. The author's own stated gaps (no strategic layer, fragmented procurement coverage, no full data model) are candidate places to test whether a BFO-based approach does better. Also worth citing as an example of the citation-trap risk itself: "basic formal ontology" in a title does not guarantee BFO.

## Limitations
- Self-acknowledged: does not fully solve the common-language problem; strategic layer and procurement/acquisition are weakly covered by SCOR; no full data model was produced.
- Demonstration is illustrative (one organization's metrics mapped to SCOR), not a validated multi-firm deployment.
- SCOR itself is a process reference model built by and for practitioners, not a formally-verified ontology from the outset, so aligning it to OWL inherits whatever ambiguity was already in SCOR.
