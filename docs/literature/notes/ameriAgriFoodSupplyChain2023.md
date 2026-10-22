---
citekey: ameriAgriFoodSupplyChain2023
title: "Agri-Food Supply Chain Traceability Supported by a Formal Ontology: A Grain Elevator to Processor Use Case"
year: 2023
status: reading
read_by: []
relevance: core
approach: [bfo, supply-chain, methodology]
component: both
tags: [traceability, sct, scro, iof, custody, ownership, identity, datalog, synthetic-data]
informs: [ADR-0001, ADR-0002, ADR-0004, ADR-0005]
---

## Summary
The second version of the Supply Chain Traceability (SCT) ontology from [[ameriEnablingTraceabilityAgriFood2022]],
by Ameri, Wallace, Yoder, and Riddick (ASME IDETC-CIE 2023, DETC2023-108860). It extends SCT from harvest to on-farm
storage to shipments of grain from an elevator to a feed processor, adding sampling, observation, transformation,
custody change, and ownership change events, plus patterns for measurement results and identifiers. They test it on
simulated data with SPARQL queries and Datalog rules in RDFox.

## Key claims
- SCT is now a domain ontology importing **BFO, IOF Core, and some SCRO constructs**, no longer CCO; "Each class in
  SCT must have a BFO, IOF Core, or SCRO parent class" (p. 3). Definitions follow the IOF annotation guide: label,
  natural language definition, and for non-primitive terms a semi-formal and a first-order definition (pp. 3-4).
- **Critical Tracking Event** is a subclass of IOF Core's *event*: a process or process boundary recognized and
  typically recorded by an agent (p. 4).
- **Sampling event:** a transfer event with a sample as specified output, prescribed by a sampling plan (pp. 4-5).
- **Observation event:** an agent observes a trace unit or piece of equipment and the event outputs information about
  it. Results are measurement information content entities with measured value expressions and units, or an ordinal
  classification scheme for true/false results such as contamination (pp. 5-7).
- **Transformation event** (blending, milling, re-identification) is primitive, because "change of identity" is not
  formalized (p. 5).
- **Custody change event:** custodians bear source and target custodian roles; a custodian has possession or control
  without necessarily owning. Treated as instantaneous here. Primitive: only a necessary condition (a source and a
  target custodian participate) is given, because fully defining it would need Allen's interval relations to say
  the custodian before differs from the one after (p. 5).
- **Ownership change event:** "very similar" to custody change; parties gain and lose owner roles, modeled as
  *change* instances over a temporal interval with first and last instants, linked by *owns at some time* (pp. 5-6).
- **Identifiers:** IOF Core *identifier*, with *designates* functional so each identifier designates exactly one
  thing; GS1 Global Location Numbers as an example, prescribed by an identification scheme (p. 7).
- **Datalog rules** add *initiates role* and *terminates role* links from custody change events to custodian roles,
  so the chain of custody can be read with simpler queries (p. 10).

## Method / data
Same top-down (IOF principles) and bottom-up (use case, CQs written early) approach as 2022. Data come from an
AnyLogic simulation of wheat deliveries to processors in the Great Plains, extended from NIST's earlier simulation:
an Excel table of events, with extra rows per custody change, plus a JSON file of observation results (pp. 7-8).
Apache Jena turns them into RDF via hand-drawn mapping diagrams (p. 8). In RDFox, SPARQL query results were compared
with the source data, and Datalog rules were materialized (pp. 9-10). Three queries are shown: the custodians in a
custody change event, all custodians of a load, and the interval during which a driver had custody of a load.

## What BFO's commitments buy or cost here
- **Buy:** the role pattern handles custody and ownership uniformly: a custodian or owner is an agent bearing a role
  that is gained and lost in events, and the chain of custody of a load falls out of a query.
- **Cost, time:** the ontology cannot say that custody actually changed. With BFO's "at some time" relations, nothing
  distinguishes the custodian before from the one after; the authors would need interval relations BFO's OWL
  release does not have. This is the [F-002](../../../research/findings/F-002.md) gap in a working use case.
- **Cost, identity:** re-identification and blending are left primitive or out of scope because change of identity is
  not formalized. BFO offers no ready account of when a load stops being the same load.
- **Outside OWL:** the Datalog rules carry part of the meaning (which event starts and ends which role). Whether that
  is BFO's cost or OWL's is an attribution question for us.

## Relevance to our project
- **Sharpens our scope** ([research/PLAN.md](../../../research/PLAN.md)). Custody and ownership change are now
  modeled, but left primitive. What remains open, and is common in DoD records:
  - **Accountability** as a third relation besides custody and ownership: the government keeps ownership while
    custody and accountability move between activities.
  - **Re-identification**, which they defer: document numbers, transportation control numbers, NSN substitutions.
  - **Discrete, serialized items** rather than bulk grain.
  - **Whether SCRO and IOF Core alone can express this**, given SCT is not published.
- **CQ templates for custody and ownership** (pp. 3, 9): "Who had source ownership of the load from which Sample x
  was taken?", "Who have been the custodians for this TRU?", "When was this TRU in the custody of this driver?"
- **ADR-0002:** custody and ownership as roles bounded by change events is a worked option for representing change,
  and shows where it runs out.
- **ADR-0005:** their Datalog rules play the same part as our mapping rules: meaning added outside OWL.
- **ADR-0001:** SCT moved from CCO to IOF Core, as SCRO did ([[ameriModelingSupplyChain2019]]).

## Limitations
- Simulated data only; validation compares query results with the generating data set, which checks the mapping
  more than the ontology.
- The key new classes (custody change, ownership change, transformation) are primitive, so the reasoner cannot
  classify events as them; Datalog does part of that work.
- Custody change is assumed instantaneous.
- Still bulk grain; the claim that the core notions carry to other bulk-goods supply chains is untested.
- The ontology file is not published or linked.

## Quotes
> "Each class in SCT must have a BFO, IOF Core, or SCRO parent class." (p. 3)

> "To fully define the Custody Change event, there is a need to introduce Allen's Interval Algebra relationships in
> the ontology in order to indicate that the custodian 'before' the event is different from the 'custodian' after
> the event." (p. 5)

> "Currently Transformation Event is treated as a primitive construct since the constructs related to change of
> identify [sic] are not fully formalized yet." (p. 5)

> "By directly linking roles to their initiating or terminating events, the chain of custody can be reconstructed
> through simpler queries." (p. 10)

> "By running multiple queries, it was confirmed that the ontology can adequately represent the domain knowledge and
> meet the requirements defined through the competency questions." (p. 10)

## Open questions
- Can the before/after difference be stated with BFO 2020's temporalized relations, or only with interval relations
  from outside BFO?
- How would accountability (DoD property accountability) relate to custody and ownership in their pattern: a third
  role, or a kind of custodian role?
- Which "SCRO constructs" does SCT import, and do they match the release we pinned?
- Are the elevator-to-processor and planting-to-harvest data sets that NIST lists available?
