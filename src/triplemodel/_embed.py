"""Nested TripleModel embedding (IRI and blank-node strategies)."""

from __future__ import annotations

from pydantic import BaseModel
from rdflib import BNode, Graph, URIRef
from rdflib.term import Node

from triplemodel._config import EmbedMode, RdfConfig, get_rdf_config
from triplemodel._types import python_to_term
from triplemodel._typing import TripleRow


def export_nested_triples(
    parent_subject: str,
    predicate: str,
    nested: BaseModel,
    *,
    embed: EmbedMode = "iri",
    config: RdfConfig | None = None,
) -> list[TripleRow]:
    """Export nested model triples and the link triple from parent."""
    from triplemodel._graph import model_to_triples

    nested_cls = type(nested)
    nested_cfg = get_rdf_config(nested_cls)
    _ = config  # parent config; nested always uses nested class Rdf
    triples: list[TripleRow] = []

    if embed == "bnode":
        node = BNode()
        for subj, pred, obj in model_to_triples(nested, config=nested_cfg):
            triples.append((node, pred, obj))
        triples.append((parent_subject, predicate, node))
        return triples

    if embed != "iri":
        raise ValueError(f"Unknown embed mode {embed!r}; use 'iri' or 'bnode'.")

    child_uri = nested_cfg.subject_uri(nested)
    triples.extend(model_to_triples(nested, config=nested_cfg))
    triples.append((parent_subject, predicate, child_uri))
    return triples


def import_nested_value(
    graph: Graph,
    term: Node,
    nested_cls: type[BaseModel],
    *,
    embed: EmbedMode = "iri",
) -> BaseModel:
    """Hydrate a nested model from an RDF object term."""
    from triplemodel._graph import graph_to_model

    if isinstance(term, BNode):
        return graph_to_model(graph, nested_cls, term, validate_type=False)

    if isinstance(term, URIRef):
        return graph_to_model(graph, nested_cls, str(term))

    raise ValueError(
        f"Cannot import nested {nested_cls.__name__} from term {term!r} "
        f"with embed={embed!r}."
    )


def add_nested_to_graph(
    graph: Graph,
    parent_subject: str,
    predicate: str,
    nested: BaseModel,
    *,
    embed: EmbedMode = "iri",
    config: RdfConfig | None = None,
) -> None:
    """Add nested export triples directly to ``graph``."""
    for subj, pred, obj in export_nested_triples(
        parent_subject, predicate, nested, embed=embed, config=config
    ):
        from triplemodel._graph import _subject_node

        subj_node = subj if isinstance(subj, Node) else _subject_node(subj)
        graph.add((subj_node, URIRef(pred), python_to_term(obj)))
