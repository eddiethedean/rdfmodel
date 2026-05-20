"""Base Pydantic model with RDF serialization."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Mapping
from typing import Any, cast

from typing_extensions import Self

from pydantic import BaseModel, ConfigDict
from triplemodel.store import RdfDataset as Dataset, RdfGraph as Graph
from triplemodel.store.terms import RdfTerm as Node

from triplemodel.config import GraphMode, RdfConfig, get_rdf_config
from triplemodel.io import (
    OnDuplicate,
    graph_to_model,
    graph_to_models,
    model_to_graph,
    model_to_triples,
    sync_to_graph,
)
from triplemodel.io.dataset import (
    all_from_dataset,
    graph_to_model_from_dataset,
    model_to_dataset,
    sync_to_dataset,
)
from triplemodel.io.files import (
    dump_graph,
    infer_format,
    is_quad_format,
    parse_into_graph,
    parse_url_into_graph,
)
from triplemodel._typing import TripleRow
from triplemodel.protocols import PredicateResolver, register_rdf_resource
from triplemodel.terms.registry import LiteralRegistry, default_registry


class TripleModel(BaseModel):
    """Pydantic model that can be serialized to and from an RDF graph.

    Subclasses declare RDF metadata on a nested ``Rdf`` class and map fields
    with :func:`~triplemodel.rdf_field` or ``Annotated[..., Predicate(...)]``.
    A nested ``Rdf`` on a subclass **replaces** the parent's config entirely;
    do not declare an empty ``class Rdf:`` on a child if you intend to inherit
    the parent's ``namespace``, ``type_uri``, or ``id_field``.

    Example::

        class Person(TripleModel):
            class Rdf:
                namespace = "http://example.org/people/"
                type_uri = "http://xmlns.com/foaf/0.1/Person"
                id_field = "slug"

            slug: str
            name: str = rdf_field("http://xmlns.com/foaf/0.1/name")
    """

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=False,
    )

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        super().__pydantic_init_subclass__(**kwargs)
        from triplemodel.metadata.cardinality import (
            raise_if_inverse_collection,
            raise_if_nested_collection,
        )

        for field_info in cls.model_fields.values():
            raise_if_nested_collection(field_info)
            raise_if_inverse_collection(field_info)
        from triplemodel.fields.validation import validate_model_predicates

        validate_model_predicates(cls)
        register_rdf_resource(cls)

    def subject_uri(self, *, uri: str | None = None) -> str:
        """Return the RDF subject IRI for this instance."""
        if uri is not None:
            return uri
        return get_rdf_config(type(self)).subject_uri(self)

    def to_triples(
        self,
        *,
        uri: str | None = None,
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry | None = None,
    ) -> list[TripleRow]:
        """Export instance data as (subject, predicate, object) tuples."""
        return model_to_triples(self, uri=uri, resolver=resolver, registry=registry)

    def to_graph(
        self,
        graph: Graph | None = None,
        *,
        uri: str | None = None,
        mode: GraphMode | None = None,
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        skolemize: bool | None = None,
        shacl_shapes: Graph | str | Path | Any | None = None,
    ) -> Graph:
        """Serialize this instance into a :class:`~triplemodel.Store` graph.

        When ``mode`` is omitted, uses ``Rdf.graph_mode`` (default ``"add"``).
        """
        result = model_to_graph(
            self,
            graph,
            uri=uri,
            mode=mode,
            resolver=resolver,
            registry=registry,
            skolemize=skolemize,
        )
        if shacl_shapes is not None:
            from triplemodel.validation.shacl import validate_graph

            validate_graph(result, shacl_shapes)
        return result

    def to_dataset(
        self,
        dataset: Dataset | None = None,
        *,
        uri: str | None = None,
        graph_iri: str | None = None,
        mode: GraphMode | None = None,
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        skolemize: bool | None = None,
        shacl_shapes: Graph | str | Path | Any | None = None,
    ) -> Dataset:
        """Serialize this instance into a named-graph dataset."""
        result = model_to_dataset(
            self,
            dataset,
            uri=uri,
            graph_iri=graph_iri,
            mode=mode,
            resolver=resolver,
            registry=registry,
            skolemize=skolemize,
        )
        if shacl_shapes is not None:
            from triplemodel.validation.shacl import validate_graph

            cfg = get_rdf_config(type(self))
            from triplemodel.config import get_graph_context, resolve_graph_iri

            context = get_graph_context(
                result, graph_iri or resolve_graph_iri(self, cfg)
            )
            validate_graph(context, shacl_shapes)
        return result

    def serialize(
        self,
        *,
        format: str = "turtle",
        destination: str | Path | None = None,
        uri: str | None = None,
        mode: GraphMode | None = None,
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        skolemize: bool | None = None,
        shacl_shapes: Graph | str | Path | Any | None = None,
        **rdflib_kwargs: Any,
    ) -> str | bytes | None:
        """Serialize this instance to an RDF document string or file."""
        cfg = get_rdf_config(type(self))
        if is_quad_format(format) or cfg.graph_iri:
            from triplemodel.io.dataset import dump_dataset

            ds = self.to_dataset(
                None,
                uri=uri,
                mode=mode,
                resolver=resolver,
                registry=registry,
                skolemize=skolemize,
                shacl_shapes=shacl_shapes,
            )
            return dump_dataset(
                ds,
                destination,
                format=format,
                jsonld_context=cfg.jsonld_context,
                **rdflib_kwargs,
            )
        graph = model_to_graph(
            self,
            None,
            uri=uri,
            mode=mode,
            bind=True,
            resolver=resolver,
            registry=registry,
            skolemize=skolemize,
        )
        if shacl_shapes is not None:
            from triplemodel.validation.shacl import validate_graph

            validate_graph(graph, shacl_shapes)
        return dump_graph(
            graph,
            destination,
            format=format,
            jsonld_context=cfg.jsonld_context,
            **rdflib_kwargs,
        )

    def sync_to_graph(
        self,
        graph: Graph,
        *,
        uri: str | None = None,
        mode: GraphMode | None = None,
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        skolemize: bool | None = None,
    ) -> Graph:
        """Update ``graph`` with owned triples for this instance (see ``mode``).

        When ``mode`` is omitted, uses ``Rdf.graph_mode`` if set to something other
        than ``"add"``; otherwise defaults to ``"replace"``.
        """
        return sync_to_graph(
            self,
            graph,
            uri=uri,
            mode=mode,
            resolver=resolver,
            registry=registry,
            skolemize=skolemize,
        )

    def sync_to_dataset(
        self,
        dataset: Dataset,
        *,
        uri: str | None = None,
        graph_iri: str | None = None,
        mode: GraphMode | None = None,
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        skolemize: bool | None = None,
    ) -> Dataset:
        """Update the named graph for this instance within ``dataset``."""
        return sync_to_dataset(
            self,
            dataset,
            uri=uri,
            graph_iri=graph_iri,
            mode=mode,
            resolver=resolver,
            registry=registry,
            skolemize=skolemize,
        )

    @classmethod
    def from_graph(
        cls,
        graph: Graph,
        uri: str | Node,
        *,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
    ) -> Self:
        """Construct an instance from triples about ``uri`` (IRI string or term)."""
        return graph_to_model(
            graph,
            cls,
            uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
        )

    @classmethod
    def all_from_graph(
        cls,
        graph: Graph,
        *,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
    ) -> list[Self]:
        """Load every resource of this model's RDF type from ``graph``."""
        return graph_to_models(
            graph,
            cls,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
        )

    @classmethod
    def from_dataset(
        cls,
        dataset: Dataset,
        uri: str,
        *,
        graph_iri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
    ) -> Self:
        """Construct an instance from triples in this model's named graph context."""
        return graph_to_model_from_dataset(
            dataset,
            cls,
            uri,
            graph_iri=graph_iri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
        )

    @classmethod
    def all_from_dataset(
        cls,
        dataset: Dataset,
        *,
        graph_iri: str | None = None,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
    ) -> list[Self]:
        """Load every resource of this model's RDF type from its named graph context."""
        return all_from_dataset(
            dataset,
            cls,
            graph_iri=graph_iri,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
        )

    @classmethod
    def rdf_config(cls) -> RdfConfig:
        """Return resolved RDF configuration for this model class."""
        return get_rdf_config(cls)

    @classmethod
    def _instances_from_parsed_graph(
        cls,
        graph: Graph,
        *,
        dispatch: bool = False,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
    ) -> list[Self]:
        if dispatch:
            from triplemodel.io.dispatch import all_from_graph_dispatch

            return cast(
                list[Self],
                all_from_graph_dispatch(
                    graph,
                    validate_type=validate_type,
                    on_duplicate=on_duplicate,
                    resolver=resolver,
                    registry=registry,
                    de_skolemize=de_skolemize,
                ),
            )
        return cls.all_from_graph(
            graph,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
        )

    @classmethod
    def _instances_from_parsed_dataset(
        cls,
        dataset: Dataset,
        *,
        dispatch: bool = False,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
    ) -> list[Self]:
        if dispatch:
            from triplemodel.io.dispatch import all_from_dataset_dispatch

            return cast(
                list[Self],
                all_from_dataset_dispatch(
                    dataset,
                    validate_type=validate_type,
                    on_duplicate=on_duplicate,
                    resolver=resolver,
                    registry=registry,
                    de_skolemize=de_skolemize,
                ),
            )
        return cls.all_from_dataset(
            dataset,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
        )

    @classmethod
    def _should_parse_dataset(cls, fmt: str) -> bool:
        cfg = get_rdf_config(cls)
        return is_quad_format(fmt) or cfg.graph_iri is not None

    @classmethod
    def parse(
        cls,
        source: str | Path | None = None,
        *,
        data: str | bytes | None = None,
        format: str | None = None,
        base: str | None = None,
        dispatch: bool = False,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
        **rdflib_kwargs: Any,
    ) -> list[Self]:
        """Parse an RDF document and load model instances."""
        cfg = get_rdf_config(cls)
        resolved_base = base if base is not None else cfg.base_uri
        resolved_format = infer_format(source if data is None else None, format)
        if cls._should_parse_dataset(resolved_format):
            from triplemodel.io.dataset import parse_into_dataset

            dataset = parse_into_dataset(
                source=source,
                data=data,
                format=resolved_format,
                base=resolved_base,
                bind_prefixes=cfg.prefixes_dict,
                jsonld_context=cfg.jsonld_context,
                **rdflib_kwargs,
            )
            return cls._instances_from_parsed_dataset(
                dataset,
                dispatch=dispatch,
                type_uri=type_uri,
                validate_type=validate_type,
                on_duplicate=on_duplicate,
                resolver=resolver,
                registry=registry,
                de_skolemize=de_skolemize,
            )
        graph = parse_into_graph(
            source=source,
            data=data,
            format=resolved_format,
            base=resolved_base,
            bind_prefixes=cfg.prefixes_dict,
            jsonld_context=cfg.jsonld_context,
            **rdflib_kwargs,
        )
        return cls._instances_from_parsed_graph(
            graph,
            dispatch=dispatch,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
        )

    @classmethod
    def parse_file(  # ty: ignore[invalid-method-override]
        cls,
        path: str | Path,
        *,
        format: str | None = None,
        base: str | None = None,
        dispatch: bool = False,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
        **rdflib_kwargs: Any,
    ) -> list[Self]:
        """Parse RDF from a local file path."""
        path_obj = Path(path)
        resolved_format = infer_format(path_obj, format)
        return cls.parse(
            source=path_obj,
            format=resolved_format,
            base=base,
            dispatch=dispatch,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
            **rdflib_kwargs,
        )

    @classmethod
    def parse_url(
        cls,
        url: str,
        *,
        format: str | None = None,
        base: str | None = None,
        timeout: float = 30.0,
        dispatch: bool = False,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
        **rdflib_kwargs: Any,
    ) -> list[Self]:
        """Parse RDF from a URL."""
        cfg = get_rdf_config(cls)
        resolved_base = base if base is not None else cfg.base_uri
        resolved_format = infer_format(url, format)
        if cls._should_parse_dataset(resolved_format):
            from triplemodel.io.dataset import parse_url_into_dataset

            dataset = parse_url_into_dataset(
                url,
                format=resolved_format,
                base=resolved_base,
                timeout=timeout,
                bind_prefixes=cfg.prefixes_dict,
                jsonld_context=cfg.jsonld_context,
                **rdflib_kwargs,
            )
            return cls._instances_from_parsed_dataset(
                dataset,
                dispatch=dispatch,
                type_uri=type_uri,
                validate_type=validate_type,
                on_duplicate=on_duplicate,
                resolver=resolver,
                registry=registry,
                de_skolemize=de_skolemize,
            )
        graph = parse_url_into_graph(
            url,
            format=resolved_format,
            base=resolved_base,
            timeout=timeout,
            bind_prefixes=cfg.prefixes_dict,
            jsonld_context=cfg.jsonld_context,
            **rdflib_kwargs,
        )
        return cls._instances_from_parsed_graph(
            graph,
            dispatch=dispatch,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
        )

    @classmethod
    def construct_from_sparql(
        cls,
        graph: Graph,
        query: str,
        *,
        dispatch: bool = False,
        graph_out: Graph | None = None,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
        **kwargs: Any,
    ) -> list[Self]:
        """Run CONSTRUCT/DESCRIBE and load instances of this class."""
        from triplemodel.io.sparql import construct_models

        return construct_models(
            cls,
            graph,
            query,
            dispatch=dispatch,
            graph_out=graph_out,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
            **kwargs,
        )

    @classmethod
    def select_from_sparql(
        cls,
        graph: Graph,
        query: str,
        *,
        field_map: Mapping[str, str] | None = None,
        subject_var: str | None = None,
        hydrate: bool = False,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
        **kwargs: Any,
    ) -> list[Self]:
        """Run SELECT and build instances from bindings or hydration."""
        from triplemodel.io.sparql import select_models

        return select_models(
            cls,
            graph,
            query,
            field_map=field_map,
            subject_var=subject_var,
            hydrate=hydrate,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
            **kwargs,
        )

    @classmethod
    def load_sparql(
        cls,
        endpoint: str,
        query: str,
        *,
        query_form: str | None = None,
        read_only: bool = True,
        dispatch: bool = False,
        type_uri: str | None = None,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
        **kwargs: Any,
    ) -> list[Self]:
        """Query a remote SPARQL endpoint and return instances."""
        from triplemodel.io.sparql import SparqlQueryForm, load_sparql

        return load_sparql(
            cls,
            endpoint,
            query,
            query_form=cast("SparqlQueryForm | None", query_form),
            read_only=read_only,
            dispatch=dispatch,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
            **kwargs,
        )

    @classmethod
    def cbd(
        cls,
        graph: Graph,
        uri: str | Node,
        *,
        dispatch: bool = False,
        validate_type: bool = True,
        on_duplicate: OnDuplicate = "warn",
        resolver: PredicateResolver | None = None,
        registry: LiteralRegistry = default_registry,
        de_skolemize: bool | None = None,
        include_reifications: bool = True,
    ) -> Self:
        """Load an instance from the concise bounded description around ``uri``."""
        from triplemodel.io.cbd import cbd_model

        return cbd_model(
            cls,
            graph,
            uri,
            dispatch=dispatch,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
            include_reifications=include_reifications,
        )

    @classmethod
    def ask_sparql(
        cls,
        graph: Graph,
        query: str,
        **kwargs: Any,
    ) -> bool:
        """Execute an ASK query on ``graph``."""
        from triplemodel.io.sparql import ask

        return ask(graph, query, model_cls=cls, **kwargs)


register_rdf_resource(TripleModel)

__all__ = ["TripleModel"]
