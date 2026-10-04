"""Shared namespaces. Use these in pipelines instead of hard-coding IRIs."""

from rdflib import Namespace

SCO = Namespace("https://w3id.org/sco/")
OBO = Namespace("http://purl.obolibrary.org/obo/")


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
