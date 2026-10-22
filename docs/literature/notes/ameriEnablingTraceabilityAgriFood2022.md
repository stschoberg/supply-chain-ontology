---
citekey: ameriEnablingTraceabilityAgriFood2022
title: Enabling Traceability in Agri-Food Supply Chains Using an Ontological Approach
year: 2022
status: reading
read_by: []
relevance: core
approach: [bfo, supply-chain, methodology]
component: both
tags: [traceability, scro, iof, cte-kde, roles, synthetic-data]
informs: [ADR-0001, ADR-0002, ADR-0004]
---

## Summary
Ameri, Wallace, Yoder, and Riddick (Texas State and NIST) build a Supply Chain Traceability (SCT) ontology on BFO and
SCRO, borrowing from CCO and IAO, to give stakeholders in bulk grain supply chains a shared model of traceability
data. It formalizes the Institute of Food Technologists' Critical Tracking Events (CTEs) and Key Data Elements
(KDEs), with grain harvested on a farm as the use case. They test it on simulated data and one small real data set,
using a tool that turns spreadsheets into RDF and draws the resulting traceability graph. The JCISE version of
[[ameriEnablingTraceabilityAgriFood2020]].

## Key claims
- Traceability is assembled from CTEs (events where goods are created, moved, transformed, or change owner or
  custody), each with KDEs: who, what, where, when, why (p. 1).
- Existing food traceability ontologies fall short: little axiomatization, a focus on ingredients rather than
  events, and, for EPCIS-based work, a design around tagged items that fits bulk goods poorly (pp. 2-3).
- **Traceable Resource Unit (TRU)** is a defined class: anything bearing a TRU role. A **load** is grain bearing a
  load role; a portion of grain bears a *source load role* as input to a transfer and a *target load role* as its
  output. The roles begin and end with transfer events, and the reasoner infers which grain is a load (pp. 5-8).
- Objects get no times directly: "objects (and their attributes) have no direct asserted relationship with temporal
  regions." Time is reached through the events they take part in, which occur on temporal intervals (pp. 9-10).
- A **container** is a role (a field can be a container); a *container artifact* is designed to contain. A container
  interior is a BFO site, so it can carry its own temperature and humidity (pp. 10-11).
- Locations use BFO sites and spatial regions, BFO 2020's time-indexed *located in*, and an adapted CCO pattern for
  GPS points and tracks of moving objects (pp. 11-13).
- The current SCT supports mainly transfer and transport events. Transformation, ownership change, custody change,
  and maintenance are future work (p. 17).

## Method / data
Top-down (aligned to BFO and SCRO under IOF principles) and bottom-up (requirements from AgGateway's CART project:
combine to grain cart to truck to bin). Competency questions were written first and later adapted to the simulated
data (pp. 4, 16). Data: a simulator (AnyLogic) generates CTE records for harvest-to-storage operations, because
little real CTE/KDE data exists, plus one real harvest data set with missing times, amounts, and locations (pp. 14,
16). A Java tool (Apache Jena) maps CSV columns onto the ontology, writes RDF, and shows the graph; CQs are answered
by browsing it or by generated SPARQL (pp. 14-16).

## What BFO's commitments buy or cost here
- **Buy:** roles give a clean account of things that are a load or a container only for a while, and defined classes
  let the reasoner sort grain into loads, source loads, and target loads. Sites and spatial regions separate "where
  the cart is" from "where the coordinates are."
- **Cost:** the time pattern is long. A timestamp is reached through event, interval, beginning instant, identifier,
  and literal, and the authors admit the generated SPARQL is "prone to error" even for experts (p. 15). A whole extra
  ontology was needed on top of SCRO to say any of it.
- **Unclear:** the ontology was "not sufficiently axiomatized for full-scale automated reasoning" (p. 17), so how
  much the BFO commitments did beyond naming is not tested.

## Relevance to our project
- **Scope for our next phase.** It sets the event types and leaves custody and ownership change as future work,
  but the 2023 follow-up, [[ameriAgriFoodSupplyChain2023]], adds custody change and ownership change events,
  though both are left primitive. See [research/PLAN.md](../../../research/PLAN.md).
- **CQ templates.** Seven CQs (pp. 4, 13), e.g. "What are the events in which <Load ID> has participated in between
  <t1> and <t2>", "Which equipment did the grain pass through", "Which Load is a blend created by two or more
  transfer events". Starting points for our traceability CQs.
- **Precedent for synthetic data** under a real-data gap, as with our `dlms_synth` source.
- **ADR-0002:** load roles bounded by events, and time only through events, are worked examples of representing
  change; compare with SCRO's shipment role ([F-001](../../../research/findings/F-001.md)) and F-002.
- **ADR-0001:** a working instance of the "both" option: BFO and SCRO as the base, with CCO patterns borrowed.
- **Fungible goods.** Mixed grain has no identity to trace, much as stock issued from a shelf in our DoD records
  has none (see the `dlms_synth` mapping README). The TRU role is their answer.
- Builds on [[ameriModelingSupplyChain2019]], where traceability was one of SCRO's four motivating use cases.

## Limitations
- Validation is by the authors' own tool, by browsing and querying, not by reasoning; the ontology is not
  axiomatized enough to test inference.
- Simulated data, plus one real data set that needed manual cleanup, and a simplifying assumption that the amount
  loaded equals the amount unloaded (p. 16).
- Only transfer and transport events are worked out; the harder event types are future work.
- The SCT ontology itself is not linked from the paper; unclear whether it is published.

## Quotes
> "In the SCT Ontology, TRU is treated as a defined class rather than an asserted universal." (p. 5)

> "In SCT ontology, objects (and their attributes) have no direct asserted relationship with temporal regions."
> (p. 9)

> "The current version of the SCT ontology can mainly support Transfer and Transport Events." (p. 17)

> "the SCT ontology was not sufficiently axiomatized for full-scale automated reasoning and inference." (p. 17)

> "because the EPCIS model is designed around barcoded or RFID-tagged artifacts, it has limited utility for tracking
> unpackaged bulk goods such as grain or flour." (p. 2)

## Open questions
- Is the SCT ontology published? Not that we could find (2026-10-21): no file in the paper, on NIST's project page,
  or in `iofoundry/ontology`, where SCRO's TRU classes are the only trace of it.
- How would custody or ownership change be modeled in their pattern: as another event type with agent roles, or
  something else?
- Do SCRO's current TRU classes come from this work? SCRO's TRU role axioms mention lot numbers and observing
  processes, which this paper does not.
