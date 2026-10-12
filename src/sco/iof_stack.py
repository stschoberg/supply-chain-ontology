"""Load the tables `make research-build` derives from the pinned IOF release.

The release is a stack: BFO → IOF Core → SCRO. This module only loads and shapes ROBOT's outputs
into tidy DataFrames. It does no reasoning of its own, and it answers no research question:
filters, comparisons, and interpretation belong in the notebooks under research/notebooks/. What
each build output is, and which ROBOT command makes it, is in research/README.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path

import pandas as pd
from rdflib import Graph

from sco import graph

IOF_DIR = graph.ROOT / "research" / "reference" / "iof-scro"
BUILD = IOF_DIR / "build"

LAYER_FILES = {"BFO": "bfo.rdf", "CORE": "Core.rdf", "SCRO": "SupplyChain.rdf"}
LAYERS = tuple(LAYER_FILES)

BFO_IRI = "http://purl.obolibrary.org/obo/BFO_"
# IOF tags every term with the ontology that defines it (rdfs:isDefinedBy). BFO terms carry no tag.
_DEFINED_BY = {
    "https://spec.industrialontologies.org/ontology/core/Core/": "CORE",
    "https://spec.industrialontologies.org/ontology/supplychain/SupplyChain/": "SCRO",
}
PREFIXES = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX iof-av: <https://spec.industrialontologies.org/ontology/annotation/>
"""


@dataclass(frozen=True)
class Stack:
    """The IOF stack as tables. Every table that has a `layer` column uses BFO, CORE, or SCRO."""

    classes: pd.DataFrame
    """One row per class, from `robot export` over the reasoned stack: `layer`, `IRI`, `LABEL`,
    inferred named parents, anonymous superclasses and equivalents in Manchester syntax, and IOF's
    definitions in prose and first-order logic. Cells with several values separate them with `|`."""

    properties: pd.DataFrame
    """One row per property: `layer`, `IRI`, `LABEL`, `Type`, `SubProperty Of`, `Domain`,
    `Range`."""

    ancestors: pd.DataFrame
    """One row per class and inferred ancestor, with both labels and layers. `ancestor depth` is
    how many ancestors the ancestor has itself, so larger means more specific."""

    measures: pd.DataFrame
    """`robot measure` for each layer's own file: `metric`, `metric_value`, `metric_type`,
    `layer`."""

    axiom_types: pd.DataFrame
    """Axiom counts by OWL axiom type for each layer's own file: `layer`, `axiom type`, `count`."""

    restriction_uses: pd.DataFrame
    """How often each property appears in a restriction, counted in each layer's own file:
    `used in`, `property`, `defined in`, `uses`. BFO's file is not counted."""

    fol_annotations: pd.Series
    """First-order logic annotations (`iof-av:firstOrderLogic…`) in each layer's own file."""


@cache
def load_graph(path: Path) -> Graph:
    """Parse an ontology file once, however often it is queried."""
    return Graph().parse(path)


def layer_graph(layer: str) -> Graph:
    """One layer's own file from the pinned release, without its imports."""
    return load_graph(IOF_DIR / LAYER_FILES[layer])


def reasoned_graph() -> Graph:
    """The whole stack merged and classified by HermiT, with inferred superclasses written out."""
    return load_graph(BUILD / "iof-reasoned.ttl")


def sparql(g: Graph, query: str) -> pd.DataFrame:
    """Run SPARQL over an rdflib graph and return a DataFrame of strings (PREFIXES predeclared)."""
    result = g.query(PREFIXES + query)
    return pd.DataFrame(
        [["" if v is None else str(v) for v in row] for row in result],
        columns=[str(v) for v in result.vars],
    )


def nearest_bfo_category(ancestors: pd.DataFrame) -> pd.Series:
    """Each class's most specific BFO ancestor, indexed by class IRI and named `BFO category`.

    Takes `Stack.ancestors`. A class with several equally specific BFO ancestors gets them joined
    with ` | `.
    """
    return (
        ancestors.loc[lambda d: d["ancestor layer"] == "BFO"]
        .loc[lambda d: d["ancestor depth"] == d.groupby("IRI")["ancestor depth"].transform("max")]
        .groupby("IRI")["ancestor label"]
        .agg(" | ".join)
        .rename("BFO category")
    )


def load() -> Stack:
    """Read everything under research/reference/iof-scro/build/ (no network, no Java)."""
    classes = _read_export("classes.tsv")
    properties = _read_export("properties.tsv")
    measures = pd.concat(map(_read_measure, LAYERS), ignore_index=True)
    return Stack(
        classes=classes,
        properties=properties,
        ancestors=_ancestors(classes),
        measures=measures,
        axiom_types=_axiom_types(measures),
        restriction_uses=_restriction_uses(properties),
        fol_annotations=pd.Series({layer: _fol_annotations(layer) for layer in LAYERS}),
    )


def _with_layer(df: pd.DataFrame) -> pd.DataFrame:
    """Put each term's layer first, and drop terms from neither BFO nor IOF.

    IOF's tag wins over the IRI: IOF Core defines one class, process profile, under a BFO IRI.
    """
    tag = df["rdfs:isDefinedBy"].map(_DEFINED_BY)
    untagged_bfo = tag.isna() & df["IRI"].str.startswith(BFO_IRI)
    return (
        df.assign(layer=tag.mask(untagged_bfo, "BFO"))
        .dropna(subset="layer")
        .loc[:, ["layer", *df.columns]]
        .reset_index(drop=True)
    )


def _read_export(name: str) -> pd.DataFrame:
    return pd.read_csv(BUILD / name, sep="\t").fillna("").pipe(_with_layer)


def _read_measure(layer: str) -> pd.DataFrame:
    return pd.read_csv(BUILD / f"measure-{layer.lower()}.tsv", sep="\t").assign(layer=layer)


def _ancestors(classes: pd.DataFrame) -> pd.DataFrame:
    names = classes[["IRI", "LABEL", "layer"]]
    pairs = (
        sparql(reasoned_graph(), "SELECT ?IRI ?ancestor WHERE { ?IRI rdfs:subClassOf+ ?ancestor }")
        .merge(names, on="IRI")
        .merge(
            names.rename(
                columns={"IRI": "ancestor", "LABEL": "ancestor label", "layer": "ancestor layer"}
            ),
            on="ancestor",
        )
    )
    depth = pairs.groupby("IRI").size()
    return pairs.assign(**{"ancestor depth": pairs["ancestor"].map(depth).fillna(0).astype(int)})


def _axiom_types(measures: pd.DataFrame) -> pd.DataFrame:
    # `robot measure` reports axiom types as "SubClassOf 169" in one column.
    parts = measures.loc[measures["metric"] == "axiom_type_count", "metric_value"].str.split()
    return pd.DataFrame(
        {
            "layer": measures.loc[parts.index, "layer"],
            "axiom type": parts.str[0],
            "count": parts.str[1].astype(int),
        }
    ).reset_index(drop=True)


def _restriction_uses(properties: pd.DataFrame) -> pd.DataFrame:
    def uses_in(layer: str) -> pd.DataFrame:
        return sparql(
            layer_graph(layer),
            "SELECT ?IRI (COUNT(?r) AS ?uses) WHERE { ?r owl:onProperty ?IRI } GROUP BY ?IRI",
        ).assign(**{"used in": layer})

    return (
        pd.concat(map(uses_in, ("CORE", "SCRO")))
        .merge(properties[["IRI", "LABEL", "layer"]], on="IRI")
        .rename(columns={"LABEL": "property", "layer": "defined in"})
        .astype({"uses": int})
        .loc[:, ["used in", "property", "defined in", "uses"]]
        .sort_values(["used in", "uses"], ascending=[True, False])
    )


def _fol_annotations(layer: str) -> int:
    counted = sparql(
        layer_graph(layer),
        """SELECT (COUNT(*) AS ?n) WHERE {
             ?s ?p ?o .
             FILTER(?p IN (iof-av:firstOrderLogicDefinition, iof-av:firstOrderLogicAxiom))
           }""",
    )
    return int(counted["n"].iloc[0])
