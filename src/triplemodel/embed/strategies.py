"""Nested model embedding strategies (IRI and blank-node)."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel
from rdflib import BNode, Graph, URIRef
from rdflib.term import Node

from triplemodel._typing import TripleRow
from triplemodel.config import EmbedMode, RdfConfig, get_rdf_config
from triplemodel._typing import OnDuplicate
from triplemodel.terms.registry import LiteralRegistry, default_registry


@dataclass(frozen=True)
class IriEmbedStrategy:
    """Embed nested resources at their own subject IRIs."""

    mode: EmbedMode = "iri"

    def export(
        self,
        parent_subject: str,
        predicate: str,
        nested: BaseModel,
        *,
        config: RdfConfig | None = None,
    ) -> list[TripleRow]:
        from triplemodel.io.export import model_to_triples

        nested_cfg = get_rdf_config(type(nested))
        _ = config
        child_uri = nested_cfg.subject_uri(nested)
        triples = list(model_to_triples(nested, config=nested_cfg))
        triples.append((parent_subject, predicate, child_uri))
        return triples

    def import_value(
        self,
        graph: Graph,
        term: Node,
        nested_cls: type[BaseModel],
        *,
        on_duplicate: OnDuplicate = "warn",
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool = False,
    ) -> BaseModel:
        from triplemodel.io.import_ import graph_to_model

        if not isinstance(term, URIRef):
            raise ValueError(
                f"Cannot import nested {nested_cls.__name__} from term {term!r} "
                f"with embed='iri'."
            )
        return graph_to_model(
            graph,
            nested_cls,
            str(term),
            on_duplicate=on_duplicate,
            registry=registry,
            de_skolemize=de_skolemize,
        )


@dataclass(frozen=True)
class BnodeEmbedStrategy:
    """Embed nested resources as blank-node subgraphs."""

    mode: EmbedMode = "bnode"

    def export(
        self,
        parent_subject: str,
        predicate: str,
        nested: BaseModel,
        *,
        config: RdfConfig | None = None,
    ) -> list[TripleRow]:
        from triplemodel.io.export import model_to_triples

        nested_cfg = get_rdf_config(type(nested))
        parent_cfg = config
        if parent_cfg is not None and parent_cfg.blank_node_policy == "stable":
            from triplemodel.terms.bnode import nested_bnode_key, stable_bnode

            node = stable_bnode(nested_bnode_key(parent_subject, predicate, nested))
        else:
            node = BNode()
        triples: list[TripleRow] = []
        for subj, pred, obj in model_to_triples(nested, config=nested_cfg):
            triples.append((node, pred, obj))
        triples.append((parent_subject, predicate, node))
        return triples

    def import_value(
        self,
        graph: Graph,
        term: Node,
        nested_cls: type[BaseModel],
        *,
        on_duplicate: OnDuplicate = "warn",
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool = False,
    ) -> BaseModel:
        from triplemodel.io.import_ import graph_to_model

        if not isinstance(term, BNode):
            raise ValueError(
                f"Cannot import nested {nested_cls.__name__} from term {term!r} "
                f"with embed='bnode'."
            )
        return graph_to_model(
            graph,
            nested_cls,
            term,
            validate_type=False,
            on_duplicate=on_duplicate,
            registry=registry,
            de_skolemize=de_skolemize,
        )


EMBED_STRATEGIES: dict[EmbedMode, IriEmbedStrategy | BnodeEmbedStrategy] = {
    "iri": IriEmbedStrategy(),
    "bnode": BnodeEmbedStrategy(),
}


def get_embed_strategy(embed: EmbedMode) -> IriEmbedStrategy | BnodeEmbedStrategy:
    if embed not in EMBED_STRATEGIES:
        raise ValueError(f"Unknown embed mode {embed!r}; use 'iri' or 'bnode'.")
    return EMBED_STRATEGIES[embed]


def export_nested_triples(
    parent_subject: str,
    predicate: str,
    nested: BaseModel,
    *,
    embed: EmbedMode = "iri",
    config: RdfConfig | None = None,
) -> list[TripleRow]:
    """Export nested model triples and the link triple from parent."""
    return get_embed_strategy(embed).export(
        parent_subject, predicate, nested, config=config
    )


def import_nested_value(
    graph: Graph,
    term: Node,
    nested_cls: type[BaseModel],
    *,
    embed: EmbedMode = "iri",
    on_duplicate: OnDuplicate = "warn",
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool = False,
) -> BaseModel:
    """Hydrate a nested model from an RDF object term."""
    return get_embed_strategy(embed).import_value(
        graph,
        term,
        nested_cls,
        on_duplicate=on_duplicate,
        registry=registry,
        de_skolemize=de_skolemize,
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
    from triplemodel.io.writer import apply_triple_rows

    rows = export_nested_triples(
        parent_subject, predicate, nested, embed=embed, config=config
    )
    apply_triple_rows(graph, rows)
