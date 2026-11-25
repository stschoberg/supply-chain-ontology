# The fuel records in SCRO

What IOF Core and its Supply Chain Reference Ontology (SCRO) make of the [fuel records](../README.md). Twenty
SPARQL rules map the records into IOF terms; [lifted.ttl](lifted.ttl) is the result. Each rule says whether SCRO
decided the mapping or we had to, because SCRO leaves the choice open.

## The story in SCRO

| Event | What the records say | What SCRO makes of it |
|---|---|---|
| 1–2 | Two refinery batches arrive and go into tank T1. | Each batch is a material entity with a **lot role**. Each delivery is fuel with a **shipment role**. After receipt, both are **parts of "the fuel in T1"**. |
| 3 | Additive turns T1's Jet A into JP-8. | A process with T1's fuel as both input and output: the same fuel, before and after. |
| 4 | A sample stands for all the fuel in T1. | The sample is **part of** T1's fuel. How much it stands for has no term. |
| 5 | 400,000 gal ships to T3; a certificate re-batches it as CA-55, from the two refinery batches. | The shipment was part of T1's fuel. CA-55 is a new lot, the **output of a "manufacturing process"** with the refinery lots as input. |
| 6–7 | T2's JP-5 is regraded to JP-8; T4's JP-5 fails a test and is downgraded to JP-8. | Both: a **change** the tank's fuel takes part in, classified by **both grades**. The two come out identical. Only the sample that passed can say so. |
| 8 | The responsible officer hands over the account. | Each officer has a role, gained and lost on a date, **acting for the DFSP**. Nothing ties them to the fuel. |
| 9 | Fuel from T3 is sold to a unit. | The sold fuel is part of T3's fuel and **owned by** the unit, with no date. No owner is recorded before the sale. |

Throughout, "the fuel in T1" is **one node for the whole two months**: there is nothing to say when its contents
change.

## Findings

1. **SCRO never recognizes a lot.** SCRO defines a *lot* as something designated by a *lot identifier*, and a *lot
   identifier* as something that designates a *lot*. Each needs the other first, so a reasoner concludes neither:
   the three batches only ever come out as "traceable resource units". *Shipment*, defined by its role alone, is
   inferred. SCRO's own written definition of lot has only the role; the circle is in the OWL. (Checked with OWL 2
   RL; to confirm with HermiT.)
2. **SCRO says which fuel, not when.** Being part of a tank's fuel, being classified by a grade, and being owned
   all hold only "at some time". So one node stands for T1's fuel from February to March, and the 400,000 gal
   shipped out and the 79,603 gal left behind are both parts of it. Only processes have dates. This comes from
   BFO 2020's OWL, whose parthood has only "at some time" and "at all times" forms.
3. **A regrade and a downgrade look the same.** The difference the DoD acts on, whether the JP-5 met its own
   specification, can be stated only for the sample that passed. That the other failed, OWL can only leave
   unsaid, and neither result is linked to the grade change.
4. **Re-batching has to become manufacturing.** SCRO's lot role requires a manufacturing process, and SCRO has no
   blending or mixing. So the certificate's "re-batched from RB-101 and RB-102" becomes a process nobody performed.
5. **Accountability attaches to the DFSP, as in the manual.** Dated role changes find the right officer on each
   day, but only as someone acting for the DFSP. SCRO has nothing for custody or accountability.

[`test_lift_fuel_records_iof_scro.py`](../../../../tests/test_lift_fuel_records_iof_scro.py) checks findings 1–3
against the output.

## How the mapping works

Each `.rq` file in this directory is one **rule**: a SPARQL query that reads one kind of record and writes what it
means in SCRO's terms. For example, [06](06-shipped-fuel-has-a-shipment-role.rq) reads a shipment document and
writes "there is some fuel, it has a shipment role, it was moved in a transport process". Each rule's opening
comment says why.

Some of these mappings SCRO decides; others it leaves open, so we had to choose. That split is the point: where we
had to choose is where SCRO doesn't cover bulk fuel.

**SCRO decided:**

- A delivery is fuel with a **shipment role**, moved in a **transport process**, and received in a **receiving
  process** (rules 06, 08).
- A batch number identifies fuel with a **lot role** (05).
- A sale is a **selling process**, and the buyer **owns** what was sold (16).
- A handover of the account is an **inventory management process** (17).
- Organizations, people, grade codes, test results, dates, and on-spec samples, from IOF Core (01–02, 12–13, 15,
  18–20).

**We had to choose:**

| Choice | Why SCRO doesn't decide it | Rule |
|---|---|---|
| A tank holds **one** body of fuel, for all time | Nothing in SCRO marks when a tank's contents become different fuel | [03](03-each-tank-holds-one-inventory.rq) |
| The DFSP storing the fuel stands in for **custody** | SCRO has no custody | [04](04-the-dfsp-stores-the-inventory.rq) |
| A shipment under a refinery certificate is **part of** that refinery batch | Nothing relates a shipment to a lot | [07](07-shipped-fuel-is-part-of-its-refinery-lot.rq) |
| The fuel received is the fuel shipped, though 0.15–0.28% less | No rule for when losing some fuel makes it different fuel | [08](08-receipt-puts-the-shipment-in-the-tank.rq) |
| Fuel shipped from a tank was **part of** the tank's fuel | Same as above | [09](09-shipping-takes-fuel-from-a-tank.rq) |
| A re-batch certificate is a **manufacturing process** | A lot must come from manufacturing, and there is no blending | [10](10-rebatching-is-a-manufacturing-process.rq) |
| Adding an additive leaves the **same fuel** | No rule for when a change makes different fuel | [11](11-additive-injection-modifies-the-inventory.rq) |
| A sample is **part of** the tank's fuel | SCRO has no sample | [14](14-sample-is-part-of-the-tank-fuel.rq) |

No rule declares something a lot or a shipment outright. SCRO defines those, so the reasoner decides, and what it
fails to decide is finding 1.

`make lift-examples` reruns the rules and rebuilds [lifted.ttl](lifted.ttl).
