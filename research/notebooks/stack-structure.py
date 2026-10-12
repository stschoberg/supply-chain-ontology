import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # How BFO shapes IOF Core and SCRO

    > **Draft.** A working analysis for PHI 598. The interpretation has not been reviewed and may change.

    Traces BFO's influence down the pinned IOF stack (IOF `Release_202603`): BFO 2020 → IOF Core → SCRO. The
    method, and what counts as a finding, is in [research/README.md](../README.md).

    Everything here is read from `research/reference/iof-scro/build/`, which `make research-build` derives from
    the pinned release with [ROBOT](https://robot.obolibrary.org): the stack classified by the HermiT reasoner,
    class and property tables, and metrics. This notebook only
    queries those outputs, with pandas and SPARQL.

    Run it with `uv run marimo edit research/notebooks/stack-structure.py`.
    """)
    return


@app.cell
def _():
    import dataclasses

    import altair as alt
    import marimo as mo
    import pandas as pd

    from sco import graph, iof_stack

    stack = iof_stack.load()

    def with_shares(counts: pd.DataFrame) -> pd.DataFrame:
        """Follow each column of counts with its share of that column's total, in percent."""
        shares = (100 * counts / counts.sum()).round().astype(int).add_suffix(" %")
        return pd.concat([counts, shares], axis=1).loc[
            :, [name for column in counts.columns for name in (column, f"{column} %")]
        ]

    # Chart styling shared by every chart: one fixed color per layer, in both themes.
    LAYER_NAMES = {"BFO": "BFO", "CORE": "IOF Core", "SCRO": "SCRO"}
    _dark = mo.app_meta().theme == "dark"
    # Three categorical hues, checked for colorblind separation against each surface.
    _HUES = ["#199e70", "#3987e5", "#d95926"] if _dark else ["#1baf7a", "#2a78d6", "#eb6834"]
    LAYER_COLORS = dict(zip(LAYER_NAMES.values(), _HUES, strict=True))
    CHART_TEXT, _GRID = ("#c3c2b7", "#2c2c2a") if _dark else ("#52514e", "#e1e0d9")

    def layer_color(*layers: str) -> alt.Color:
        """Color marks by the `layer` field, with each layer's fixed color and a legend on top."""
        names = [LAYER_NAMES[layer] for layer in layers]
        return alt.Color(
            "layer:N",
            scale=alt.Scale(domain=names, range=[LAYER_COLORS[name] for name in names]),
            legend=alt.Legend(title=None, orient="top"),
        )

    def styled(chart):
        """Quiet axes and gridlines, so the bars are the only loud thing."""
        return (
            chart.properties(background="transparent")
            .configure_view(stroke=None)
            .configure_axis(
                labelColor=CHART_TEXT,
                titleColor=CHART_TEXT,
                gridColor=_GRID,
                domainColor=_GRID,
                tickColor=_GRID,
                labelLimit=260,
                labelFontSize=12,
                titleFontSize=12,
                titleFontWeight="normal",
            )
            .configure_axisY(grid=False, ticks=False, domain=False, labelPadding=8)
            .configure_legend(labelColor=CHART_TEXT, labelFontSize=12, symbolType="square")
        )

    return (
        CHART_TEXT,
        LAYER_NAMES,
        alt,
        dataclasses,
        graph,
        iof_stack,
        layer_color,
        mo,
        pd,
        stack,
        styled,
        with_shares,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary

    **Question.** Within the supply chain domain, what do BFO's commitments buy or cost? This notebook looks
    for the answer in a published BFO-based stack: how far BFO shapes IOF Core, and how far both shape SCRO.
    What that does to instance data is not tested here.

    **What we've found.** In order of how much each bears on the question:

    1. **The role pattern is the most common single pattern in SCRO.** 44% of its classes are roles or are
       defined by having one, and a third of the relation uses in its axioms are role relations. BFO
       provides the category, IOF Core turns it into a way of defining classes, and SCRO applies it at
       scale. A distributor is an organization in a position, not a kind of organization.
       *(The role pattern; Relations)*
    2. **BFO fixes what things are far more firmly than how they relate.** Every one of the 205 Core and
       SCRO classes has a place under a BFO category. Only 39 of the 101 relations they define trace back
       to a BFO relation. The other 61% stand outside BFO's relations altogether, and they cluster in what
       BFO leaves out: information and reference (BFO has no "is about"), time between processes,
       measurement, causation, and commerce (ownership and supply). It starts at the mid-level: 59% of
       Core's relations have no BFO ancestor, before SCRO adds any. *(Relations)*
    3. **SCRO adds vocabulary, not grammar.** It defines 114 kinds of thing but only 18 relations. Nine in
       ten of the relation uses in its axioms are relations defined above it. *(The three layers; Relations)*
    4. **BFO can't be used for supply chains without a substantial mid-level.** Core's largest share of
       classes is information (plans, agreements, identifiers), which BFO has no classes for. In two places
       Core also alters BFO itself: it declares `process profile` under a BFO IRI that BFO 2020 doesn't
       have, and it places its own `capability` between BFO's `disposition` and `function`.
       *(Where Core and SCRO attach to BFO: where Core alters BFO)*
    5. **Only part of BFO is in play.** Half of its categories have nothing under them, and more than half of
       its relations are never used directly in an axiom. Nothing in the stack is a BFO quality. BFO's own relations between things can only say "at
       some time"; Core adds interval relations of its own to order processes.
       *(Where Core and SCRO attach to BFO; Time-indexed relations)*

    **What that says about the question.**

    - **BFO buys** a forced, disjoint place for every term, a clean fit for the physical side of logistics,
      and the role idea that most of the supply chain vocabulary is built on.
    - **BFO costs** a required mid-level, role indirection in the data (role individuals and a reasoner
      before anything counts as a supplier), and no built-in way to state commercial facts or when a
      relation holds. Its guarantee of shared meaning covers classes, and fewer than half of the relations.

    **What isn't established yet.**

    - **Forced or chosen.** These are counts of what the ontologies do. Whether BFO forced a result or IOF
      chose it needs justifications for the inferences, which are not built yet.
    - **Data.** Everything here is about the ontologies' own axioms. None of it has been tested against
      instance data, which is where indirection and missing commercial relations would cost the most.

    **How it is organized.** The first sections cover how the layers are built: sizes, where classes attach
    to BFO, the role pattern, whose relations are used, and what a reasoner can check. Two sections then test
    one BFO principle each and back findings F-001 and F-002. The appendix has lookup tables.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The three layers

    How big is each layer, and how is it built? A term's layer is IOF's own `rdfs:isDefinedBy` tag: IOF Core
    and SCRO share one namespace, so the IRI can't tell them apart. The loaded tables are listed in the
    appendix.
    """)
    return


@app.cell
def _(pd, stack):
    def _per_layer(df: pd.DataFrame) -> pd.Series:
        return df["layer"].value_counts()

    (
        pd.DataFrame(
            {
                "classes defined": _per_layer(stack.classes),
                "defined by equivalence": _per_layer(
                    stack.classes.loc[lambda d: d["Equivalent Class"] != ""]
                ),
                "object properties defined": _per_layer(
                    stack.properties.loc[lambda d: d["Type"] == "Object property"]
                ),
                "logical axioms": stack.measures.loc[
                    lambda d: d["metric"] == "logical_axiom_count"
                ].set_index("layer")["metric_value"],
            }
        )
        .fillna(0)
        .astype(int)
        .assign(
            **{
                "% by equivalence": lambda d: (
                    (100 * d["defined by equivalence"] / d["classes defined"]).round().astype(int)
                )
            }
        )
        .loc[
            :,
            [
                "classes defined",
                "defined by equivalence",
                "% by equivalence",
                "object properties defined",
                "logical axioms",
            ],
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    How big each layer is, and how it is built.

    - **Classes / object properties defined:** the terms each layer adds itself, by IOF's `rdfs:isDefinedBy`
      tag.
    - **Defined by equivalence:** classes with a definition a reasoner can apply, such as "a supplier is an
      organization or person that has a supplier role". Membership is inferred, not asserted.
    - **Logical axioms:** the statements in that layer's own file that a reasoner uses (labels and comments
      excluded), from `robot measure`.

    **Observations.**
     - SCRO adds the most classes but few relations of its own, so it has to describe supply chains with Core's and BFO's.
     - Close to half of Core's and SCRO's classes are defined by equivalence; none of BFO's are.
     - Core has about twice SCRO's logical axioms.

    One oddity: Core's count includes process profile, which has a BFO-style IRI (`BFO_0000144`) but isn't in
    the BFO 2020 file. IOF Core declares it and tags it as its own.

    **What this shows:**

    The takeaway is that SCRO adds vocabulary, not grammar.

    It adds 114 kinds of thing but only 18 relations, so almost everything it says about a shipment or a distributor is said with relations it inherited from IOF Core (83) and BFO (64). Nearly half of its classes are also built from one pattern set up above it: "a [BFO category] that has some [role]".

    So BFO and Core decide how a supply chain fact can be stated, and SCRO only decides which things get names. The table is the first evidence for that, and the later sections test it: Relations shows which inherited relations SCRO actually uses.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Where Core and SCRO attach to BFO

    Which BFO category each class ends up under: its most specific BFO ancestor **after reasoning**. Core is
    here as the comparison for SCRO. Putting the two side by side shows what each layer adds to BFO. BFO's own
    classes are left out, since each is its own category.
    """)
    return


@app.cell
def _(iof_stack, pd, stack):
    def _has_core_ancestor(pairs: pd.DataFrame) -> pd.Series:
        return (
            pairs["ancestor layer"]
            .eq("CORE")
            .groupby(pairs["IRI"])
            .any()
            .rename("has Core ancestor")
        )

    attach = (
        stack.classes.loc[
            lambda d: d["layer"] != "BFO", ["layer", "IRI", "LABEL", "SubClass Of [NAMED]"]
        ]
        .rename(columns={"SubClass Of [NAMED]": "direct parents"})
        .join(iof_stack.nearest_bfo_category(stack.ancestors), on="IRI")
        .join(_has_core_ancestor(stack.ancestors), on="IRI")
        .fillna({"has Core ancestor": False})
        .astype({"has Core ancestor": bool})
    )
    return (attach,)


@app.cell
def _(attach, pd, stack, with_shares):
    def _group_small(counts: pd.DataFrame, below: int = 5) -> pd.DataFrame:
        """Fold categories with fewer than `below` classes in every layer into one row."""
        small = (counts < below).all(axis=1)
        return pd.concat(
            [counts.loc[~small], counts.loc[small].sum().to_frame("other categories").T]
        )

    by_category = (
        pd.crosstab(attach["BFO category"], attach["layer"])
        .sort_values("SCRO", ascending=False)
        .pipe(_group_small)
        .pipe(with_shares)
        .rename_axis(index="BFO category", columns=None)
    )
    # BFO categories that no Core or SCRO class sits anywhere beneath.
    unused_bfo = sorted(
        set(stack.classes.loc[lambda d: d["layer"] == "BFO", "LABEL"])
        - set(
            stack.ancestors.loc[
                lambda d: (d["layer"] != "BFO") & (d["ancestor layer"] == "BFO"), "ancestor label"
            ]
        )
    )
    return by_category, unused_bfo


@app.cell
def _(LAYER_NAMES, alt, by_category, layer_color, pd, styled):
    _long = pd.concat(
        by_category[[layer, f"{layer} %"]]
        .set_axis(["classes", "share"], axis=1)
        .assign(layer=LAYER_NAMES[layer])
        .reset_index()
        for layer in ("CORE", "SCRO")
    )
    styled(
        alt.Chart(_long)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            y=alt.Y("BFO category:N", sort=list(by_category.index), title=None),
            yOffset=alt.YOffset(
                "layer:N",
                sort=[LAYER_NAMES["CORE"], LAYER_NAMES["SCRO"]],
                scale=alt.Scale(paddingInner=0.15),
            ),
            x=alt.X(
                "share:Q", title="Share of the layer's classes (%)", axis=alt.Axis(tickCount=4)
            ),
            color=layer_color("CORE", "SCRO"),
            tooltip=[
                alt.Tooltip("BFO category:N"),
                alt.Tooltip("layer:N", title="Layer"),
                alt.Tooltip("classes:Q", title="Classes"),
                alt.Tooltip("share:Q", title="Share of layer (%)"),
            ],
        )
        .properties(width=520, height=alt.Step(13))
    )
    return


@app.cell
def _(by_category, mo, unused_bfo):
    mo.vstack(
        [
            by_category,
            mo.md(
                f"**BFO categories with no Core or SCRO class under them "
                f"({len(unused_bfo)} of 36):** {', '.join(unused_bfo)}."
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observations.**

    - Every class lands under some BFO category.
    - Core's largest share is generically dependent continuants (information: plans, specifications,
      agreements). SCRO's largest are roles and processes.
    - Only SCRO adds sites.
    - Half of BFO's categories have nothing under them, among them quality and every temporal region.

    The next table asks a question that only applies to SCRO: which of its classes have no IOF Core ancestor,
    and so attach to BFO directly?
    """)
    return


@app.cell
def _(attach):
    attach.loc[
        lambda d: (d["layer"] == "SCRO") & ~d["has Core ancestor"],
        ["LABEL", "BFO category", "direct parents"],
    ]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observations.** These are physical and spatial things (routes, lots, cargo, locations) and the roles
    they bear, apart from `change` and `supply relationship`. SCRO's other commercial and informational
    classes go through Core.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Where Core alters BFO

    Core doesn't only add to BFO. In two places it changes it. `Core.rdf` asserts that BFO's `function` is a
    subclass of Core's own `capability`, which is itself a subclass of BFO's `disposition`, so a Core class
    now sits between two BFO classes. And it declares `process profile` under the IRI `BFO_0000144`, which
    the BFO 2020 file does not contain.
    """)
    return


@app.cell
def _(pd, stack):
    _iof_classes = set(stack.classes.loc[lambda d: d["layer"] != "BFO", "LABEL"])
    pd.concat(
        [
            stack.classes.loc[
                lambda d: (
                    (d["layer"] == "BFO")
                    & d["SubClass Of [NAMED]"].map(
                        lambda parents: bool(set(parents.split("|")) & _iof_classes)
                    )
                )
            ].assign(change="a BFO class given an IOF Core parent"),
            stack.classes.loc[
                lambda d: (d["layer"] != "BFO") & d["IRI"].str.contains("/obo/BFO_")
            ].assign(change="an IOF Core class declared under a BFO IRI"),
        ]
    )[["change", "LABEL", "SubClass Of [NAMED]"]].rename(
        columns={"LABEL": "class", "SubClass Of [NAMED]": "direct parent after reasoning"}
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What this shows:**

    Core and SCRO do different jobs on top of BFO, and they use only part of it.

    1. **Every class has a place in BFO.** None of the 205 Core and SCRO classes is left over. This is BFO's
       basic constraint, and it is forced: nothing can be "just a thing". It is true by construction for any
       BFO-based ontology, so it is the starting condition, not a result.
    2. **The mid-level fills BFO's gaps; the domain level adds positions and activities.** Core's largest
       share is information (31%): plans, agreements, specifications, identifiers. BFO has no classes for
       these, so something has to supply them before a domain layer can say anything commercial. SCRO then
       mostly adds roles and processes (47% together). The gap is BFO's. How it is filled is IOF's choice.
       This is a cost of BFO: it can't be used for supply chains without a substantial mid-level, and that
       mid-level is where choices other than BFO's start to shape the data.
    3. **Much of what SCRO adds is positional.** Roles are SCRO's largest category, and most of its
       material-entity classes are defined by a role. The next section measures that pattern on its own.
    4. **Half of BFO goes unused.** 18 of 36 categories have nothing under them. The commitments exercised
       here are a subset: continuant/occurrent, independent/dependent, role and disposition, and
       information. There are no qualities, so attributes such as weight, quantity, or price have no home
       as BFO qualities in this stack. No class sits under BFO's temporal regions either: Core
       handles time with relations between processes instead (see Time-indexed relations). What BFO costs
       should be judged on the subset in use.
    5. **Physical logistics needs only BFO.** Only SCRO adds sites, and the 30 SCRO classes with no Core
       ancestor are physical or spatial things and the roles they bear, apart from two (`change` and
       `supply relationship`). For places, routes, and goods, BFO's own categories were enough; Core is
       needed for the commercial and informational side.

    **What it can't show.** Counts are not importance: a category with few classes may carry most of the
    data. Shares also reflect what the authors chose to cover. And this section shows where classes sit, not
    why. Showing whether BFO forced a placement needs justifications, which are not built yet.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## The role pattern

    Roles show up twice in these layers: as role classes themselves (distributor role), and as classes
    *defined* by having a role (a distributor is a business organization or person that has some
    distributor role). The table counts both, and the share of each layer's relation uses that are the two
    role relations, `has role` and `role of`.
    """)
    return


@app.cell
def _(attach, pd, stack):
    _classes = stack.classes.loc[lambda d: d["layer"] != "BFO"].join(
        attach.set_index("IRI")["BFO category"], on="IRI"
    )
    _is_role = _classes["BFO category"] == "role"
    _has_role = (
        _classes["Equivalent Class"].str.contains("'has role' some", regex=False) & ~_is_role
    )
    _uses = stack.restriction_uses.assign(
        role=lambda d: d["property"].isin(["has role", "role of"])
    )
    (
        pd.DataFrame(
            {
                "classes": _classes.groupby("layer").size(),
                "role classes": _is_role.groupby(_classes["layer"]).sum(),
                "defined by having a role": _has_role.groupby(_classes["layer"]).sum(),
                "relation uses": _uses.groupby("used in")["uses"].sum(),
                "role relation uses": _uses.loc[lambda d: d["role"]]
                .groupby("used in")["uses"]
                .sum(),
            }
        )
        .assign(
            **{
                "% of classes in the pattern": lambda d: (
                    (100 * (d["role classes"] + d["defined by having a role"]) / d["classes"])
                    .round()
                    .astype(int)
                ),
                "% of relation uses": lambda d: (
                    (100 * d["role relation uses"] / d["relation uses"]).round().astype(int)
                ),
            }
        )
        .loc[
            :,
            [
                "classes",
                "role classes",
                "defined by having a role",
                "% of classes in the pattern",
                "role relation uses",
                "% of relation uses",
            ],
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observations.** The pattern covers 44% of SCRO's classes and 29% of Core's. Of SCRO's 48 classes
    defined by equivalence, 23 are defined by having a role. The role-defined classes are mostly material
    entities, but four are sites: SCRO treats even a ship-to location as a place in a role.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What this shows:**

    The role pattern is the most common single pattern in SCRO.

    1. **Supply chain vocabulary is mostly positional.** 44% of SCRO's classes are roles or are defined by
       having one (shipment, cargo, distributor), against 29% in Core, and a third of the relation uses in
       its axioms are role relations. A distributor is an organization in a position, not a kind of
       organization.
    2. **BFO provides the category, Core the pattern, SCRO the scale.** BFO says roles exist. IOF Core turns
       that into a way of defining classes: it defines `has role`, and defines agent, supplier, and buyer
       by their roles. SCRO then applies the same idiom to its own terms. SCRO barely uses the rest of
       BFO's distinction among realizable entities: it has 6 dispositions and 2 functions.
    3. **It buys flexibility.** One company can be a supplier and a customer with no new classes.
    4. **It costs indirection.** The data must contain role individuals, and a reasoner must run, before
       anything counts as a distributor.

    **What it can't show.** Most common is not forced. BFO makes the pattern possible; it does not require
    that a distributor be modeled as a role. Whether SCRO had an alternative is not something
    these counts can settle.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Relations

    Classes say what kinds of thing there are. Relations are how an axiom says anything about them. This
    section asks whose relations Core and SCRO use, and how their own relations connect to BFO's.

    First: every time an axiom in Core or SCRO uses a relation, which layer defined that relation?
    """)
    return


@app.cell
def _(stack, with_shares):
    stack.restriction_uses.pivot_table(
        index="defined in", columns="used in", values="uses", aggfunc="sum", fill_value=0
    ).pipe(with_shares)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** Columns are the layer whose axioms are being counted; rows are the layer that defines
    the relation used. `%` is the share of that column, so the `SCRO %` column says where the relations in
    SCRO's axioms come from.

    Next, the relations SCRO's axioms use most, colored by the layer that defines each.
    """)
    return


@app.cell
def _(CHART_TEXT, LAYER_NAMES, alt, layer_color, stack, styled):
    _top = (
        stack.restriction_uses.loc[lambda d: d["used in"] == "SCRO"]
        .nlargest(10, "uses", keep="all")
        .assign(layer=lambda d: d["defined in"].map(LAYER_NAMES))
    )
    _bars = (
        alt.Chart(_top)
        .mark_bar(cornerRadiusEnd=4, height=14)
        .encode(
            y=alt.Y("property:N", sort=list(_top["property"]), title=None),
            x=alt.X("uses:Q", title="Uses in SCRO's axioms", axis=alt.Axis(tickCount=5)),
            color=layer_color("BFO", "CORE", "SCRO"),
            tooltip=[
                alt.Tooltip("property:N", title="Relation"),
                alt.Tooltip("layer:N", title="Defined in"),
                alt.Tooltip("uses:Q", title="Uses"),
            ],
        )
    )
    _values = _bars.mark_text(align="left", dx=5, fontSize=12, color=CHART_TEXT).encode(
        text="uses:Q", color=alt.value(CHART_TEXT)
    )
    styled((_bars + _values).properties(width=480, height=alt.Step(22)))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Then Core's and SCRO's *own* relations. A relation can be declared as a special case of another
    (`has role` is a special case of BFO's `bearer of`), which ties it into the hierarchy above. The question
    is whether each IOF relation traces back to a BFO relation, directly or through other IOF relations, or
    stands outside BFO's relations altogether.
    """)
    return


@app.cell
def _(iof_stack, pd, stack):
    _relations = stack.properties.loc[lambda d: d["Type"] == "Object property"]
    _bfo = _relations.loc[lambda d: d["layer"] == "BFO"]
    # Relations with a BFO relation among their ancestors at any depth, from the reasoned stack.
    _reaches_bfo = set(
        iof_stack.sparql(
            iof_stack.reasoned_graph(),
            "SELECT ?IRI ?ancestor WHERE { ?IRI rdfs:subPropertyOf+ ?ancestor }",
        ).loc[lambda d: d["ancestor"].isin(set(_bfo["IRI"])), "IRI"]
    )

    def _with_connection(d: pd.DataFrame) -> pd.DataFrame:
        direct = d["SubProperty Of"].map(
            lambda parents: bool(set(parents.split("|")) & set(_bfo["LABEL"]))
        )
        return d.assign(
            connection=pd.Series("no BFO ancestor", index=d.index).case_when(
                [
                    (direct, "specializes a BFO relation"),
                    (d["IRI"].isin(_reaches_bfo), "reaches BFO through another IOF relation"),
                ]
            )
        )

    own_relations = _relations.loc[lambda d: d["layer"] != "BFO"].pipe(_with_connection)

    CONNECTIONS = [
        "specializes a BFO relation",
        "reaches BFO through another IOF relation",
        "no BFO ancestor",
    ]
    (
        pd.crosstab(own_relations["layer"], own_relations["connection"])
        .reindex(columns=CONNECTIONS, fill_value=0)
        .assign(
            total=lambda d: d.sum(axis=1),
            **{
                "% with no BFO ancestor": lambda d: (
                    (100 * d["no BFO ancestor"] / d["total"]).round().astype(int)
                )
            },
        )
    )
    return CONNECTIONS, own_relations


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** Each IOF relation is counted once. "No BFO ancestor" means that following
    "is a special case of" upward from the relation never arrives at a BFO relation. Compare this with the
    classes: every one of the 205 Core and SCRO classes has a BFO ancestor.

    Declaring a relation is one thing; relying on it is another. The next table asks how much of what the
    axioms actually say uses relations with no BFO ancestor.
    """)
    return


@app.cell
def _(CONNECTIONS, own_relations, stack, with_shares):
    (
        stack.restriction_uses.merge(
            own_relations[["LABEL", "connection"]].rename(columns={"LABEL": "property"}),
            on="property",
            how="left",
        )
        .fillna({"connection": "a BFO relation"})
        .pivot_table(
            index="connection", columns="used in", values="uses", aggfunc="sum", fill_value=0
        )
        .reindex(["a BFO relation", *CONNECTIONS], fill_value=0)
        .rename_axis(index="the relation used is…", columns=None)
        .pipe(with_shares)
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    What are the relations with no BFO ancestor about? The grouping below is ours, written out in the cell so
    it can be checked and changed.
    """)
    return


@app.cell
def _(own_relations, pd):
    # Our grouping of the relations that have no BFO ancestor. Edit here if a relation is misplaced.
    _THEMES = {
        "information and reference": [
            "is about",
            "is subject of",
            "prescribes",
            "prescribed by",
            "designates",
            "designated by",
            "denotes",
            "denoted by",
            "describes",
            "described by",
            "categorizes",
            "categorized by",
            "classifies",
            "classified by",
            "generalizes",
            "specializes",
            "satisfies requirement",
            "requirement satisfied by",
            "has value expression at all times",
            "has value expression at some time",
            "is value expression of at all times",
            "is value expression of at some time",
            "has measured value at some time",
            "is measured value of at some time",
        ],
        "time": [
            "temporally overlaps",
            "is temporally overlapped by",
            "temporally starts",
            "temporally started by",
            "temporally finishes",
            "temporally finished by",
            "occurs during",
            "contains occurence of",
            "occurs simultaneously with",
            "occurs on",
        ],
        "commerce and custody": [
            "owns",
            "owned by",
            "holds",
            "supplies to at some time",
            "is supplied by at some time",
            "is supplied to at some time",
            "initiates relationship",
            "relationship initiated by",
        ],
        "states and characteristics": [
            "has pre material state",
            "has post material state",
            "material state holds in",
            "has process characteristic",
            "process characteristic of",
        ],
        "measurement and observation": [
            "measures at some time",
            "measured by at some time",
            "observes at some time",
            "observed by at some time",
        ],
        "agency": [
            "acts on behalf of at some time",
            "is available to at some time",
            "recognizes at some time",
            "recognized by at some time",
        ],
        "where a process happens": ["occurs at", "starts at", "ends at", "is site of"],
        "causation and control": ["causes", "controls", "modulates"],
    }
    _theme_of = {relation: theme for theme, relations in _THEMES.items() for relation in relations}

    outside_bfo = own_relations.loc[lambda d: d["connection"] == "no BFO ancestor"].assign(
        theme=lambda d: d["LABEL"].map(_theme_of).fillna("ungrouped")
    )
    (
        pd.crosstab(outside_bfo["theme"], outside_bfo["layer"])
        .assign(
            total=lambda d: d.sum(axis=1),
            examples=outside_bfo.groupby("theme")["LABEL"].agg(
                lambda labels: ", ".join(sorted(labels)[:3])
            ),
        )
        .sort_values("total", ascending=False)
        .rename_axis(index="theme", columns=None)
    )
    return (outside_bfo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    SCRO's relations with no BFO ancestor, with what they connect (domain and range) and how often any Core
    or SCRO axiom uses them:
    """)
    return


@app.cell
def _(outside_bfo, stack):
    _uses = stack.restriction_uses.groupby("property")["uses"].sum()
    (
        outside_bfo.loc[lambda d: d["layer"] == "SCRO", ["LABEL", "theme", "Domain", "Range"]]
        .assign(**{"uses in axioms": lambda d: d["LABEL"].map(_uses).fillna(0).astype(int)})
        .rename(columns={"LABEL": "SCRO relation with no BFO ancestor"})
        .sort_values(["theme", "SCRO relation with no BFO ancestor"])
    )
    return


@app.cell
def _(mo, stack):
    _bfo = set(
        stack.properties.loc[
            lambda d: (d["layer"] == "BFO") & (d["Type"] == "Object property"), "LABEL"
        ]
    )
    _used = set(stack.restriction_uses.loc[lambda d: d["defined in"] == "BFO", "property"])
    mo.md(
        f"Core and SCRO axioms use **{len(_used & _bfo)} of BFO's {len(_bfo)} relations** directly "
        "in a restriction. The rest are either unused or reached only through a more specific "
        "relation, as `inheres in` is through `role of`."
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observations.**

    - 90% of the relation uses in SCRO's axioms are relations defined above it: 54% from Core, 36% from BFO.
    - `role of` and `has role` alone are 70 of SCRO's 222 uses (32%). Both are Core relations that specialize
      BFO relations (`inheres in` and `bearer of`).
    - 62 of the 101 relations IOF defines have no BFO ancestor: 49 of Core's 83 and 13 of SCRO's 18. Every
      one of the 205 classes has one.
    - Those relations carry 29% of the relation uses in Core's axioms and 19% in SCRO's.
    - The largest group is information and reference (24 relations). Core's whole information family
      (`prescribes`, `designates`, `describes`, `denotes`) hangs under `is about`, which has no BFO parent.
      Then time (10, nine of them Allen's interval relations) and commerce and custody (8, all SCRO's).
    - Of SCRO's 13, only `is site of`, `starts at`, `ends at`, and `owns` appear in any axiom. SCRO's axioms
      use only 6 of its 18 relations.
    - Core and SCRO use fewer than half of BFO's relations directly in an axiom.

    **What this shows:**

    BFO fixes what things *are* far more firmly than how they *relate*. Every class has a place in BFO; most
    relations IOF defines do not.

    1. **SCRO states its axioms in inherited relations.** Nine uses in ten are of a relation SCRO did not
       define. This is the evidence behind "vocabulary, not grammar": how a supply chain fact can be stated
       is mostly settled above SCRO.
    2. **The chain BFO → Core → SCRO is visible in one relation.** BFO defines `bearer of`. Core specializes
       it as `has role`. SCRO then uses `has role` and its inverse for a third of everything it says. So the
       role pattern is BFO's idea, in Core's wording, at SCRO's scale.
    3. **Classes are anchored in BFO; relations mostly are not.** All 205 classes have a BFO ancestor.
       Only 39 of 101 relations do. Where a relation does trace back, BFO buys something real and checked:
       a query written with BFO's `bearer of` also finds `has role` facts after reasoning. For the other
       61% there is no such link. A BFO-level query does not see them, and a reasoner knows nothing about
       them beyond their domain and range.
    4. **The gaps are where BFO has nothing to offer.** The unanchored relations are not scattered. They
       cluster in what BFO leaves out: information and reference (BFO has no "is about"), time between
       processes beyond `precedes`, measurement, causation, and commerce. The gap is BFO's in each case.
       How it is filled, and that the fillers are left unconnected, is IOF's choice.
    5. **It starts at the mid-level, not in SCRO.** 59% of Core's relations have no BFO ancestor, against
       72% of SCRO's. So the stack leaves BFO's relations as soon as it has to say anything about
       information, well before it reaches supply chains.
    6. **The commercial relations carry almost no logic.** `supplies to` and `owned by` are declared but
       appear in no class definition, and `owns` appears in one. This matches the prediction that ownership
       would fit BFO awkwardly.

    **What it can't show.** These are counts in the ontologies' axioms, not in data. A relation no axiom uses
    could still carry most of the facts in a real dataset: ownership and supply are exactly what procurement
    records describe.

    ### Why ownership is awkward in BFO

    Point 6 deserves a closer look, because ownership and supply are what procurement data records.

    Ownership is not a physical fact. When a pallet of bearings changes owner, nothing about the pallet
    changes: same mass, same place, same parts. What changes is a social and legal fact. BFO's relations
    cover parthood, location, participation in processes, and one thing depending on another. None of them
    means "has rights over". That leaves four ways to model ownership, each with a cost:

    | Option | How it works | What it costs |
    |---|---|---|
    | A role | The company bears an "owner role" | A role belongs to one bearer. It doesn't say *what* is owned without a second relation, which is the original problem again. |
    | A relational dependent entity | Something that depends on both parties at once | One plain fact becomes an extra individual and two links. |
    | Information | A deed or contract that is "about" the thing | Faithful to how ownership works, but "who owns this?" becomes a query through documents. |
    | A direct relation | `owns`, from owner to thing | Readable, but it has no parent in BFO, so a reasoner knows nothing about it and BFO-level queries don't see it. |

    SCRO uses two of these. For ownership it takes the direct relation: `owns` is defined as "the agent holds
    the independent continuant as legal property", has no parent relation, and appears in one axiom (the
    consignor role is the role of someone who owns a shipment). It keeps custody separate with `holds`, "the
    agent physically keeps or carries the material entity", which matters in logistics because a carrier
    holds goods it does not own. For supply it also takes the second option: a `supply relationship` is a
    specifically dependent continuant that depends on a customer role and a supplier role and is prescribed
    by an agreement.

    Time makes it worse. Ownership matters most when it changes, as title passes from seller to buyer.
    `owns` is a plain relation between two things, so it can't say when it holds (F-002). Core's interval
    relations don't help directly: they order processes and intervals, not relations between things. Saying
    when something was owned means modeling a process or event for it.

    **For the argument.** This is a cost of BFO's realism: it is precise about physical things and has
    nothing built in for commercial facts. It is testable on our own data. A USAspending award is a
    commercial fact of exactly this kind, and the number of steps it takes to say "DoD bought these bearings
    from Acme" in SCO and in IOF would measure the cost. The account of BFO's options here is common
    modeling practice as we understand it, and needs a citation before it goes in the write-up.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What a reasoner can check

    The sections above count what the ontologies state. Not all of it is enforced. A reasoner works only
    from OWL axioms. IOF also writes many definitions in first-order logic, as annotations that no reasoner
    reads. The table counts the OWL axioms a reasoner uses to classify and to reject, by layer, next to the
    first-order annotations.
    """)
    return


@app.cell
def _(pd, stack):
    _ENFORCED = ["SubClassOf", "EquivalentClasses", "DisjointClasses"]

    pd.concat(
        [
            stack.axiom_types.loc[lambda d: d["axiom type"].isin(_ENFORCED)].pivot(
                index="axiom type", columns="layer", values="count"
            ),
            stack.fol_annotations.rename("first-order logic annotations").to_frame().T,
        ]
    ).fillna(0).astype(int)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **How to read it.** `SubClassOf` and `EquivalentClasses` axioms let a reasoner infer things.
    `DisjointClasses` axioms are what let it reject something as inconsistent: without one, nothing stops
    an individual from being in two classes at once.

    **Observations.**

    - Disjointness thins out down the stack: BFO has 10 such axioms, Core adds 4, and SCRO adds none.
    - Core and SCRO carry 313 first-order logic annotations between them, against 403 subclass and
      equivalence axioms.

    **What this shows:**

    A reasoner can catch only gross category errors in this stack.

    1. **Errors are caught at BFO's level, not SCRO's.** Something asserted to be both a process and a
       material entity is rejected, because BFO says continuants and occurrents are disjoint. Something
       asserted to be both a shipment and a supplier is not, because nothing says those are disjoint.
       So "BFO prevents modeling errors" holds for mixing up its top-level categories and little else.
    2. **Much of what IOF commits to is documentation.** The first-order annotations often say more than
       the OWL beside them. IOF's own note on advance shipment notice says its OWL axiom "approximates the
       FOL definition but does not enforce identity" between the two shipments it mentions. Use
       **Explore a class** in the appendix to compare the two for any class.

    **What it can't show.** These are counts of axioms, not a test. Seeding deliberate errors and seeing
    which a reasoner rejects would measure this directly, and has not been done.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Two principles, tested

    The sections above describe the stack. The next two each test one BFO principle from
    [research/README.md](../README.md) against it, starting from a prediction written before looking. They
    are the evidence for findings F-001 and F-002.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Shipment

    **Prediction** (2026-10-10, from the principle-by-principle table): "a shipment is a process", since BFO's
    continuant/occurrent split would separate the goods from the shipping.
    """)
    return


@app.cell
def _(stack):
    stack.classes.loc[
        lambda d: d["LABEL"].isin(["shipment", "shipment role", "supply chain transport process"]),
        ["layer", "LABEL", "SubClass Of [NAMED]", "Equivalent Class"],
    ]
    return


@app.cell
def _(attach):
    attach.loc[
        lambda d: d["LABEL"].str.contains("ship|transport|cargo|consign", case=False),
        ["layer", "LABEL", "BFO category"],
    ]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observations.** SCRO defines a shipment as a material entity that has a shipment role: the goods, not
    the moving of them. The moving is a separate process class. The reasoner also infers that a shipment is a
    traceable resource unit, which no axiom states. It follows from the two classes' definitions and the fact
    that a shipment role is a traceable resource unit role.

    **What this shows:** see [F-001](../findings/F-001.md).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Time-indexed relations

    BFO's first-order axioms (ISO/IEC 21838-2) index relations by time, e.g. from `participation.cl`:

    ```
    (forall (t a b) (iff (participates-in a b t) (has-participant b a t)))
    ```

    OWL properties take two arguments, so the time has to go somewhere. Compare the BFO file SCO imports
    (`bfo-core.owl`) with the one IOF Core imports (`bfo.owl`).
    """)
    return


@app.cell
def _(graph, iof_stack, pd, stack):
    def _with_status(d: pd.DataFrame) -> pd.DataFrame:
        """Say how each relation's label compares between the two BFO files."""
        sco, theirs = d["SCO's bfo-core.owl"], d["IOF's bfo.owl"]
        return d.assign(
            status=pd.Series("same label", index=d.index).case_when(
                [
                    (sco == "", "only in IOF's bfo.owl"),
                    (theirs == "", "only in SCO's bfo-core.owl"),
                    (sco != theirs, "same IRI, different label"),
                ]
            )
        )

    bfo_relations = (
        stack.properties.loc[
            lambda d: (d["layer"] == "BFO") & (d["Type"] == "Object property"), ["IRI", "LABEL"]
        ]
        .merge(
            iof_stack.sparql(
                iof_stack.load_graph(graph.IMPORTS_DIR / "bfo-core.owl"),
                "SELECT ?IRI ?ours WHERE { ?IRI a owl:ObjectProperty ; rdfs:label ?ours }",
            ),
            on="IRI",
            how="outer",
        )
        .fillna("")
        .rename(columns={"ours": "SCO's bfo-core.owl", "LABEL": "IOF's bfo.owl"})
        .pipe(_with_status)
    )
    bfo_relations["status"].value_counts()
    return (bfo_relations,)


@app.cell
def _(bfo_relations, mo):
    mo.ui.table(bfo_relations.loc[lambda d: d["status"] != "same label"], page_size=10)
    return


@app.cell
def _(stack):
    stack.restriction_uses.loc[lambda d: d["property"].str.contains("at some time|at all times")]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    That is what BFO's own relations can say. IOF Core adds a second way to talk about time: the thirteen
    relations of Allen's interval algebra (before, meets, overlaps, starts, during, finishes, their inverses,
    and simultaneous), which hold between processes or temporal intervals. It also gives time instants a
    date-time value. The table lists those relations, their parent, and how often any axiom uses them.
    """)
    return


@app.cell
def _(stack):
    _ALLEN = [
        "before",
        "after",
        "meets",
        "met by",
        "temporally overlaps",
        "is temporally overlapped by",
        "temporally starts",
        "temporally started by",
        "occurs during",
        "contains occurence of",
        "temporally finishes",
        "temporally finished by",
        "occurs simultaneously with",
    ]
    _uses = stack.restriction_uses.groupby("property")["uses"].sum()
    (
        stack.properties.loc[
            lambda d: d["LABEL"].isin(_ALLEN), ["layer", "LABEL", "SubProperty Of", "Domain"]
        ]
        .assign(
            **{
                "SubProperty Of": lambda d: d["SubProperty Of"].replace(
                    "owl:topObjectProperty", ""
                ),
                "uses in axioms": lambda d: d["LABEL"].map(_uses).fillna(0).astype(int),
            }
        )
        .set_index("LABEL")
        .loc[_ALLEN]
        .rename(columns={"SubProperty Of": "specializes", "Domain": "holds between"})
    )
    return


@app.cell
def _(stack):
    stack.properties.loc[
        lambda d: (d["Type"] == "Data property") & d["Range"].str.contains("dateTime"),
        ["layer", "LABEL", "Domain", "Range"],
    ]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observations.**

    - Same IRIs, different labels: where `bfo-core.owl` says "participates in", `bfo.owl` says "participates
      in at some time". `bfo.owl` adds "at all times" variants. Neither OWL file can say *which* time.
    - IOF Core defines all thirteen Allen interval relations. Four specialize BFO's `precedes` or
      `preceded by`; the other nine have no parent. Axioms use them seven times in all.
    - Time instants get a date-time value through `has date-time instant value`.
    - So the stack has two ways to talk about time. Relations between things (who bears a role, what is part
      of what) can only say "at some time". Processes can be ordered against each other, and tied to a
      temporal region that has a date.

    **What this shows:** see [F-002](../findings/F-002.md).
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Appendix: look things up

    ### What `iof_stack.load()` returns

    Every table this notebook uses, with its size and columns. How each is made is in `src/sco/iof_stack.py`.
    """)
    return


@app.cell
def _(dataclasses, pd, stack):
    pd.DataFrame.from_dict(
        {
            field.name: {
                "rows": len(table := getattr(stack, field.name)),
                "columns": ", ".join(map(str, getattr(table, "columns", table.index))),
            }
            for field in dataclasses.fields(stack)
        },
        orient="index",
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Every class and its BFO category

    Every Core and SCRO class, its direct parents, and its most specific BFO category.
    """)
    return


@app.cell
def _(attach, mo):
    mo.ui.table(attach.drop(columns=["IRI", "has Core ancestor"]), page_size=10)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Every IOF relation and how it connects to BFO
    """)
    return


@app.cell
def _(mo, own_relations):
    mo.ui.table(
        own_relations[["layer", "LABEL", "connection", "SubProperty Of", "Domain", "Range"]],
        page_size=10,
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Every use of a relation in an axiom

    How often each layer's axioms use each relation, and which layer defines it.
    """)
    return


@app.cell
def _(mo, stack):
    mo.ui.table(stack.restriction_uses, page_size=10)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Explore a class

    Pick any Core or SCRO class to see what the reasoner infers about it, its OWL axioms, and the definitions
    IOF gives in prose and in first-order logic.
    """)
    return


@app.cell
def _(mo, stack):
    picked = mo.ui.dropdown(
        {
            f"{row.LABEL} ({row.layer})": row.IRI
            for row in stack.classes.loc[lambda d: d["layer"] != "BFO"]
            .sort_values("LABEL")
            .itertuples()
        },
        value="distributor role (SCRO)",
        searchable=True,
        label="Class",
    )
    picked
    return (picked,)


@app.cell
def _(mo, pd, picked, stack):
    def _bullets(cell: str) -> str:
        return "\n".join(f"- `{v}`" for v in cell.split("|") if v) or "_none_"

    def _chain(up: pd.DataFrame) -> str:
        """Ancestors as `label [layer] → …`, most specific first."""
        nearest_first = up.sort_values("ancestor depth", ascending=False)
        return " → ".join(
            f"{label} [{layer}]"
            for label, layer in zip(
                nearest_first["ancestor label"], nearest_first["ancestor layer"], strict=True
            )
        )

    def _describe(row: pd.Series, up: pd.DataFrame) -> str:
        return "\n\n".join(
            [
                f"**Inferred ancestors, most specific first:** {_chain(up)}",
                "**Direct parents:** " + row["SubClass Of [NAMED]"].replace("|", ", "),
                "**Equivalent to (checked by a reasoner):**",
                _bullets(row["Equivalent Class"]),
                "**Subclass of (checked by a reasoner):**",
                _bullets(row["SubClass Of [ANON]"]),
                "**Definition:** " + row["iof-av:naturalLanguageDefinition"],
                "**First-order logic (annotations, not checked):**",
                _bullets(
                    f"{row['iof-av:firstOrderLogicDefinition']}|{row['iof-av:firstOrderLogicAxiom']}"
                ),
            ]
        )

    mo.md(
        _describe(
            stack.classes.loc[lambda d: d["IRI"] == picked.value].iloc[0],
            stack.ancestors.loc[lambda d: d["IRI"] == picked.value],
        )
    )
    return


if __name__ == "__main__":
    app.run()
