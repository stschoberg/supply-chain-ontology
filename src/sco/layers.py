"""Load the pinned IOF stack (BFO → IOF Core → SCRO) and trace terms through its layers.

The research notebooks go through these helpers so that "which layer is this from?" has one answer.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from functools import cached_property

from rdflib import OWL, RDF, RDFS, BNode, Graph, Namespace, URIRef
from rdflib.namespace import SKOS
from rdflib.query import Result

from sco import graph

IOF_DIR = graph.ROOT / "research" / "reference" / "iof-scro"
FILES = {"BFO": "bfo.rdf", "CORE": "Core.rdf", "SCRO": "SupplyChain.rdf"}
LAYERS = tuple(FILES)

IOF = Namespace("https://spec.industrialontologies.org/ontology/construct/")
IOF_AV = Namespace("https://spec.industrialontologies.org/ontology/annotation/")
OBO = Namespace("http://purl.obolibrary.org/obo/")

PREFIXES = {"iof": IOF, "iof-av": IOF_AV, "obo": OBO, "owl": OWL, "rdfs": RDFS, "skos": SKOS}

_DECLARATIONS = (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.NamedIndividual)
_AXIOM_KINDS = ((RDFS.subClassOf, "SubClassOf"), (OWL.equivalentClass, "EquivalentTo"))


@dataclass
class Stack:
    """One graph per layer, plus their merge for queries that cross layers."""

    graphs: dict[str, Graph] = field(repr=False)

    @cached_property
    def merged(self) -> Graph:
        g = Graph()
        for prefix, ns in PREFIXES.items():
            g.bind(prefix, ns)
        for layer_graph in self.graphs.values():
            g += layer_graph
        return g

    def layer(self, term: URIRef) -> str | None:
        """The layer that declares `term`.

        IOF Core and SCRO share one namespace, so the IRI alone can't say which layer a term is
        from. Core wins if both files declare it, since SCRO may redeclare terms it uses.
        """
        if str(term).startswith(str(OBO) + "BFO_"):
            return "BFO"
        for name in ("CORE", "SCRO"):
            if any((term, RDF.type, t) in self.graphs[name] for t in _DECLARATIONS):
                return name
        return None

    def label(self, term) -> str:
        if isinstance(term, BNode):
            return "_:" + str(term)[:6]
        found = self.merged.value(term, RDFS.label)
        return str(found) if found else str(term).rsplit("/", 1)[-1]

    def classes(self, layer: str) -> list[URIRef]:
        """Named classes declared in `layer`, sorted by label."""
        declared = {
            s
            for s in self.graphs[layer].subjects(RDF.type, OWL.Class)
            if isinstance(s, URIRef) and self.layer(s) == layer
        }
        return sorted(declared, key=self.label)

    def parents(self, cls: URIRef) -> set[URIRef]:
        """Named superclasses, including the genus inside an intersection.

        `A ⊑ B ⊓ ∃r.C` and `A ≡ B ⊓ ∃r.C` both make B a parent of A. Both forms appear in SCRO.
        """
        g = self.merged
        out = set()
        for pred in (RDFS.subClassOf, OWL.equivalentClass):
            for sup in g.objects(cls, pred):
                if isinstance(sup, URIRef):
                    out.add(sup)
                for members in g.objects(sup, OWL.intersectionOf):
                    out.update(m for m in g.items(members) if isinstance(m, URIRef))
        out.discard(cls)
        return out

    def path_to_bfo(self, cls: URIRef) -> list[URIRef] | None:
        """Shortest chain of named parents from `cls` up to the first BFO class, or None."""
        queue, seen = deque([[cls]]), {cls}
        while queue:
            path = queue.popleft()
            if self.layer(path[-1]) == "BFO":
                return path
            for parent in sorted(self.parents(path[-1])):
                if parent not in seen:
                    seen.add(parent)
                    queue.append([*path, parent])
        return None

    def show_path(self, cls: URIRef) -> str:
        """e.g. `distributor role [SCRO] → agent role [CORE] → role [BFO]`."""
        path = self.path_to_bfo(cls) or [cls]
        return " → ".join(f"{self.label(c)} [{self.layer(c)}]" for c in path)

    def manchester(self, expr) -> str:
        """Render a class expression in (roughly) Manchester syntax, with labels."""
        g = self.merged
        if isinstance(expr, URIRef):
            return self.label(expr)
        for op, word in ((OWL.intersectionOf, " and "), (OWL.unionOf, " or ")):
            members = g.value(expr, op)
            if members is not None:
                parts = [self.manchester(m) for m in g.items(members)]
                return "(" + word.join(parts) + ")" if len(parts) > 1 else parts[0]
        prop = g.value(expr, OWL.onProperty)
        if prop is not None:
            for kind, word in ((OWL.someValuesFrom, "some"), (OWL.allValuesFrom, "only")):
                filler = g.value(expr, kind)
                if filler is not None:
                    return f"({self.label(prop)} {word} {self.manchester(filler)})"
            value = g.value(expr, OWL.hasValue)
            if value is not None:
                return f"({self.label(prop)} value {self.label(value)})"
        complement = g.value(expr, OWL.complementOf)
        if complement is not None:
            return f"(not {self.manchester(complement)})"
        return self.label(expr)

    def axioms(self, cls: URIRef) -> list[str]:
        """`cls`'s subclass and equivalence axioms, rendered with `manchester`."""
        name, g = self.label(cls), self.merged
        return sorted(
            f"{name} {word} {self.manchester(o)}"
            for pred, word in _AXIOM_KINDS
            for o in g.objects(cls, pred)
        )

    def query(self, sparql: str, layer: str | None = None) -> Result:
        """Run SPARQL over the merged stack, or over one layer's file, with PREFIXES predeclared."""
        target = self.merged if layer is None else self.graphs[layer]
        return target.query(sparql, initNs=PREFIXES)


def load() -> Stack:
    """The pinned IOF release in research/reference/iof-scro/ (no network access)."""
    return Stack({name: Graph().parse(IOF_DIR / f, format="xml") for name, f in FILES.items()})


def to_frame(result: Result):
    """A SPARQL result as a DataFrame of strings. Select labels in the query for readable output."""
    import pandas as pd

    return pd.DataFrame(
        [[None if v is None else str(v) for v in row] for row in result],
        columns=[str(v) for v in result.vars],
    )
