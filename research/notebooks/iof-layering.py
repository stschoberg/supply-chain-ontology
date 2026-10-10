import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # How BFO shapes IOF Core, SCRO, and their data

    Traces BFO's influence down the pinned IOF stack in `research/reference/iof-scro/` (IOF `Release_202603`):
    BFO 2020 → IOF Core → SCRO. The method, and what counts as a finding, is in
    [research/README.md](../README.md).

    Run it with `uv run marimo edit research/notebooks/iof-layering.py`. Cells re-run when what they depend on
    changes, so the page is always consistent with the code on it.
    """)
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    from rdflib import OWL, RDF, RDFS, Graph, URIRef
    from rdflib.namespace import SKOS

    from sco import graph, layers

    stack = layers.load()
    return Graph, OWL, RDF, RDFS, SKOS, URIRef, graph, layers, mo, pd, stack


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load the stack

    Each layer is its own file. IOF Core and SCRO share one namespace, so `stack.layer(term)` decides a term's
    layer by which file declares it.
    """)
    return


@app.cell
def _(OWL, RDF, pd, stack):
    def _declared(kind, layer):
        return sum(
            1 for s in stack.graphs[layer].subjects(RDF.type, kind) if stack.layer(s) == layer
        )

    pd.DataFrame(
        {
            layer: {
                "classes": len(stack.classes(layer)),
                "defined classes": sum(
                    1
                    for c in stack.classes(layer)
                    if (c, OWL.equivalentClass, None) in stack.merged
                ),
                "object properties": _declared(OWL.ObjectProperty, layer),
            }
            for layer in stack.graphs
        }
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Where SCRO attaches to BFO

    For every Core and SCRO class: the layer of its direct parents, the BFO category it ends up under, and the
    path between. Search and filter the table.
    """)
    return


@app.cell
def _(mo, pd, stack):
    _rows = []
    for _layer in ("CORE", "SCRO"):
        for _cls in stack.classes(_layer):
            _path = stack.path_to_bfo(_cls)
            _rows.append(
                {
                    "layer": _layer,
                    "class": stack.label(_cls),
                    "parent layer": "+".join(sorted({stack.layer(p) for p in stack.parents(_cls)})),
                    "BFO category": stack.label(_path[-1]),
                    "skips Core": _layer == "SCRO" and all(stack.layer(c) != "CORE" for c in _path),
                    "path": stack.show_path(_cls),
                }
            )
    classes_df = pd.DataFrame(_rows)
    mo.ui.table(classes_df, page_size=10)
    return (classes_df,)


@app.cell
def _(classes_df, pd):
    pd.crosstab(classes_df["BFO category"], classes_df["layer"]).sort_values(
        "SCRO", ascending=False
    )
    return


@app.cell
def _(classes_df):
    classes_df[classes_df["skips Core"]][["class", "BFO category", "path"]]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observations.** Every Core and SCRO class reaches BFO. Supplier, buyer, and customer are in IOF Core, not
    SCRO. Some SCRO classes attach straight to BFO without passing through Core.

    **What this shows:** _your interpretation._
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Relations

    Which properties the axioms of each layer use, and which layer declares them. Then the Core properties that
    specialize a BFO relation.
    """)
    return


@app.cell
def _(pd, stack):
    _rows = []
    for _layer in ("CORE", "SCRO"):
        _result = stack.query(
            "SELECT ?p (COUNT(?r) AS ?uses) WHERE { ?r owl:onProperty ?p } GROUP BY ?p",
            layer=_layer,
        )
        for _p, _uses in _result:
            _rows.append(
                {
                    "used in": _layer,
                    "property": stack.label(_p),
                    "declared in": stack.layer(_p),
                    "uses": int(_uses),
                }
            )
    relations_df = pd.DataFrame(_rows).sort_values(["used in", "uses"], ascending=[True, False])
    relations_df.pivot_table(
        index="used in", columns="declared in", values="uses", aggfunc="sum", fill_value=0
    )
    return (relations_df,)


@app.cell
def _(mo, relations_df):
    mo.ui.table(relations_df, page_size=10)
    return


@app.cell
def _(layers, stack):
    layers.to_frame(
        stack.query("""
            SELECT ?property ?bfo_parent WHERE {
                ?p rdfs:subPropertyOf ?parent ; rdfs:label ?property .
                ?parent rdfs:label ?bfo_parent .
                FILTER(STRSTARTS(STR(?parent), "http://purl.obolibrary.org/obo/BFO_"))
            } ORDER BY ?bfo_parent ?property
        """)
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What this shows:** _your interpretation._

    ## Explore a class

    Pick any Core or SCRO class to see its path to BFO, its OWL axioms, and the definitions IOF gives in prose
    and in first-order logic.
    """)
    return


@app.cell
def _(mo, stack):
    picked = mo.ui.dropdown(
        {
            f"{stack.label(c)} ({layer})": c
            for layer in ("SCRO", "CORE")
            for c in stack.classes(layer)
        },
        value="distributor role (SCRO)",
        searchable=True,
        label="Class",
    )
    picked
    return (picked,)


@app.cell
def _(layers, mo, picked, stack):
    def _annotations(cls, local):
        return [str(o) for o in stack.merged.objects(cls, layers.IOF_AV[local])]

    _cls = picked.value
    mo.md(
        "\n\n".join(
            [
                f"**Path:** {stack.show_path(_cls)}",
                "**OWL axioms (checked by a reasoner):**",
                "\n".join(f"- `{a}`" for a in stack.axioms(_cls)) or "_none_",
                "**Definition:** " + " ".join(_annotations(_cls, "naturalLanguageDefinition")),
                "**First-order logic (annotations, not checked):**",
                "\n".join(
                    f"- `{a}`"
                    for a in _annotations(_cls, "firstOrderLogicDefinition")
                    + _annotations(_cls, "firstOrderLogicAxiom")
                )
                or "_none_",
            ]
        )
    )
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
def _(layers, stack):
    stack.axioms(layers.IOF.Shipment), stack.show_path(layers.IOF.Shipment)
    return


@app.cell
def _(classes_df):
    classes_df[classes_df["class"].str.contains("ship|transport|cargo|consign", case=False)][
        ["layer", "class", "BFO category"]
    ]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observations.** SCRO defines a shipment as a material entity that has a shipment role: the goods, not
    the moving of them. The moving is a separate process class.

    **What this shows:** _your interpretation._

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
def _(Graph, OWL, RDF, RDFS, graph, pd, stack):
    ours = Graph().parse(graph.IMPORTS_DIR / "bfo-core.owl")
    _iof_bfo = stack.graphs["BFO"]

    def _relations(g):
        return {s: str(g.value(s, RDFS.label)) for s in g.subjects(RDF.type, OWL.ObjectProperty)}

    _ours, _theirs = _relations(ours), _relations(_iof_bfo)
    bfo_relations_df = pd.DataFrame(
        [
            {
                "IRI": str(iri).rsplit("/", 1)[-1],
                "SCO's bfo-core.owl": _ours.get(iri),
                "IOF's bfo.owl": _theirs.get(iri),
            }
            for iri in sorted(_ours.keys() | _theirs.keys())
        ]
    )
    bfo_relations_df["same label"] = (
        bfo_relations_df["SCO's bfo-core.owl"] == bfo_relations_df["IOF's bfo.owl"]
    )
    bfo_relations_df["same label"].value_counts(dropna=False)
    return bfo_relations_df, ours


@app.cell
def _(bfo_relations_df, mo):
    mo.ui.table(bfo_relations_df[~bfo_relations_df["same label"]], page_size=10)
    return


@app.cell
def _(SKOS, layers, ours, stack):
    {
        "SCO's bfo-core.owl": str(ours.value(layers.OBO.BFO_0000056, SKOS.definition)),
        "IOF's bfo.owl": str(stack.graphs["BFO"].value(layers.OBO.BFO_0000056, SKOS.definition)),
    }
    return


@app.cell
def _(relations_df):
    relations_df[relations_df["property"].str.contains("at some time|at all times")]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Observations.** Same IRIs, different labels: where `bfo-core.owl` says "participates in", `bfo.owl` says
    "participates in at some time", and its definition says so too. `bfo.owl` adds "at all times" variants.
    Neither OWL file can say *which* time.

    **What this shows:** _your interpretation._

    ## Enforced vs. annotated

    What a reasoner checks (OWL class axioms) next to what IOF states only as first-order logic annotations.
    """)
    return


@app.cell
def _(OWL, RDF, RDFS, layers, pd, stack):
    def _count(layer):
        g = stack.graphs[layer]
        return {
            "OWL class axioms": sum(
                len(list(g.triples((None, p, None))))
                for p in (RDFS.subClassOf, OWL.equivalentClass, OWL.disjointWith)
            )
            + len(list(g.subjects(RDF.type, OWL.AllDisjointClasses))),
            "disjointness axioms": len(list(g.triples((None, OWL.disjointWith, None))))
            + len(list(g.subjects(RDF.type, OWL.AllDisjointClasses))),
            "FOL annotations": sum(
                1 for _, p, _ in g if str(p).startswith(str(layers.IOF_AV) + "firstOrderLogic")
            ),
        }

    pd.DataFrame({layer: _count(layer) for layer in stack.graphs})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Use **Explore a class** above to compare the two for one class; `distributor role` is a good start.

    **What this shows:** _your interpretation._

    ## Supplier in IOF and SCO

    Open. Both define supplier from a role. Compare the two: genus, property, and what the data has to assert for
    the reasoner to infer it.
    """)
    return


@app.cell
def _(layers, stack):
    stack.axioms(layers.IOF.Supplier) + stack.axioms(layers.IOF.SupplierRole)
    return


@app.cell
def _(URIRef, graph, mo):
    _sco = graph.load_tbox().cbd(URIRef("https://w3id.org/sco/Supplier"))
    _sco.bind("sco", "https://w3id.org/sco/")
    _sco.bind("obo", "http://purl.obolibrary.org/obo/")
    mo.md(f"```turtle\n{_sco.serialize(format='turtle')}\n```")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What this shows:** _your interpretation._

    ## Particulars, not types

    Open. **Prediction** (2026-10-10): product codes such as USAspending's product and service codes are types,
    not particulars, so they become specification individuals and add a hop to most queries. Start from what IOF
    offers for product types:
    """)
    return


@app.cell
def _(classes_df):
    classes_df[classes_df["class"].str.contains("product|specification|identifier", case=False)][
        ["layer", "class", "BFO category"]
    ]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What this shows:** _your interpretation._
    """)
    return


if __name__ == "__main__":
    app.run()
