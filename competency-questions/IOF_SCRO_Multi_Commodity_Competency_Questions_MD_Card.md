# Competency Questions: Tracing Multiple Commodities

| Field | Value |
| --- | --- |
| Target ontology | IOF Supply Chain Reference Ontology (SCRO) |
| Upper ontology | BFO 2020 (with CCO patterns where noted) |
| Date | 2026-10-29 |
| Question count | 21 (5 core, 4 countable items, 4 bulk fuel, 5 grain, 3 cross-cutting) |

## Purpose

Tests whether one BFO-aligned pattern can trace countable items, bulk fuel, and grain through a shipment. Each question is tagged with the BFO/CCO pattern it exercises.

## Core (all commodities)

| # | Question | BFO/CCO pattern |
| --- | --- | --- |
| 1 | What commodity is in a given shipment, and who are the shipper, consignee, and carrier? | material entity, agent roles |
| 2 | What are the origin, destination, and intermediate nodes, and what were the planned vs. actual times for each leg? | site, process boundary, process profile |
| 3 | Which vehicle, vessel, or railcar carried the shipment on each leg? | transportation process, participant |
| 4 | Who had custody at a given time, and when did it transfer? | custody role, temporal region |
| 5 | What was the shipment's condition at pickup vs. delivery, and what caused any loss, delay, or deviation? | quality, disposition, process |

## Countable items (object aggregate)

| # | Question | BFO/CCO pattern |
| --- | --- | --- |
| 6 | How many items of a given type were ordered, shipped, received, and accepted, and how was each count determined? | member parts, cardinality, measurement process |
| 7 | Which items are identified individually (serial, NSN) vs. tracked only as a lot? | identifier, information content entity |
| 8 | What is the containment hierarchy (item → carton → pallet → container), and where is a specific item located? | object aggregate, located_in, member_part_of |
| 9 | If a shipment is split, which items went on which sub-shipment? | aggregate partition |

## Bulk fuel (portion of fluid material)

| # | Question | BFO/CCO pattern |
| --- | --- | --- |
| 10 | What volume and mass were loaded, transferred, and delivered, and at what temperature and density was each measured? | quantity of material, measurement datum, temperature-corrected value |
| 11 | What fuel specification does the shipment meet (e.g., JP-8, ULSD), and what quality test results support it? | grade, test process, sample |
| 12 | Which tank, bladder, or compartment held the fuel at a given time, and what was the previous product in it? | container, containment relation, prior process |
| 13 | If fuel was commingled, which sources were combined, and does the resulting mixture still meet spec? | fiat object part, mixing process |

## Grain (portion of granular material with biological origin)

| # | Question | BFO/CCO pattern |
| --- | --- | --- |
| 14 | Which field, crop, variety, and harvest process produced a lot, and what was its moisture at harvest? | site, harvesting process, quality |
| 15 | What grade and test results (moisture, test weight, mycotoxin) apply to a lot, who assigned them, and how was the sample taken? | grading process, sampling, information content entity |
| 16 | In which bin or silo was a lot stored, for how long, and under what temperature and humidity conditions? | storage process, site, process profile |
| 17 | Which lots or portions of lots were loaded on a given railcar, truck, or barge hold, and what was weighed at loading and unloading? | portion of material, weighing process |
| 18 | Was the grain exposed to conditions that raise spoilage risk, and did its condition change between departure and arrival? | disposition, realization, change in quality |

## Cross-cutting (tests the upper-level pattern)

| # | Question | BFO/CCO pattern |
| --- | --- | --- |
| 19 | Is the shipped thing individuated or a quantity of stuff, and does that change what "partial delivery" means? | object aggregate vs. portion of material |
| 20 | What happens to the identity of the shipped thing when it is commingled, transformed, or consumed? | continuant identity, material transformation |
| 21 | Can one query pattern retrieve custody, location, quantity, and condition across all three commodity types? | generalization test |

Question 21 carries the demonstration: one pattern answering it for countable items, fuel, and grain shows the BFO alignment is doing real work.
