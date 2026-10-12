"""Shared namespaces. Use these in pipelines instead of hard-coding IRIs."""

from rdflib import Namespace

SCO = Namespace("https://w3id.org/sco/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
# Real-world instances, keyed by their identifiers, and USAspending's own terms (ADR-0005).
DATA = Namespace("https://w3id.org/sco/data/")
USAS = Namespace("https://w3id.org/sco/source/usaspending/")
# The synthetic source's terms. Its instances live under DATA["synthetic/"], apart from real ones.
DLMS_SYNTH = Namespace("https://w3id.org/sco/source/dlms_synth/")
# IOF Core and SCRO share one namespace; the pinned release is in research/reference/iof-scro/.
IOF = Namespace("https://spec.industrialontologies.org/ontology/construct/")

# Prefixes for graphs we write.
PREFIXES = {"sco": SCO, "obo": OBO, "d": DATA, "usas": USAS, "dlms_synth": DLMS_SYNTH, "iof": IOF}


class BFO:
    """Readable aliases for the BFO 2020 IRIs we use."""

    # classes
    entity = OBO.BFO_0000001
    material_entity = OBO.BFO_0000040
    object = OBO.BFO_0000030
    object_aggregate = OBO.BFO_0000027
    role = OBO.BFO_0000023
    process = OBO.BFO_0000015
    # relations
    bearer_of = OBO.BFO_0000196
    inheres_in = OBO.BFO_0000197
    has_realization = OBO.BFO_0000054
    realizes = OBO.BFO_0000055
    has_participant = OBO.BFO_0000057
    participates_in = OBO.BFO_0000056
