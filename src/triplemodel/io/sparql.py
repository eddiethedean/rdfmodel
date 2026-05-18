"""SPARQL query passthrough and remote endpoint helpers."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypeVar, cast, overload

from pydantic import BaseModel
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.sparql import Query
from rdflib.query import Result
from rdflib.term import Node, Variable

from triplemodel.config import get_rdf_config, id_from_subject_uri
from triplemodel.fields.metadata import id_field_is_iri_id
from triplemodel.io.import_ import OnDuplicate, graph_to_model
from triplemodel.metadata.cardinality import scalar_python_type, union_member_types
from triplemodel.namespaces import bind_namespaces
from triplemodel.protocols import PredicateResolver as PredicateResolverProtocol
from triplemodel.terms.convert import python_to_term, term_to_python
from triplemodel.terms.registry import LiteralRegistry, default_registry

T = TypeVar("T", bound=BaseModel)

SparqlResultKind = Literal[
    "bindings",
    "boolean",
    "graph",
    "json",
    "ASK",
    "SELECT",
    "CONSTRUCT",
    "DESCRIBE",
]
SparqlQueryForm = Literal["select", "construct", "describe", "ask", "unknown"]

_BOOLEAN_RESULT_TYPES = frozenset({"ASK", "boolean"})
_BINDINGS_RESULT_TYPES = frozenset({"SELECT", "bindings"})
_GRAPH_RESULT_TYPES = frozenset({"CONSTRUCT", "DESCRIBE", "graph"})


def _is_boolean_result(result: Result) -> bool:
    return result.type in _BOOLEAN_RESULT_TYPES


def _is_bindings_result(result: Result) -> bool:
    return result.type in _BINDINGS_RESULT_TYPES


def _is_graph_result(result: Result) -> bool:
    return result.type in _GRAPH_RESULT_TYPES


_QUERY_FORM_RE = re.compile(
    r"\b(SELECT|CONSTRUCT|DESCRIBE|ASK)\b",
    re.IGNORECASE,
)
_COMMENT_LINE_RE = re.compile(r"#.*$", re.MULTILINE)
_COMMENT_BLOCK_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def detect_query_form(query: str) -> SparqlQueryForm:
    """Return the first SPARQL query form keyword in ``query``."""
    text = _COMMENT_BLOCK_RE.sub("", query)
    text = _COMMENT_LINE_RE.sub("", text)
    match = _QUERY_FORM_RE.search(text)
    if not match:
        return "unknown"
    return cast(SparqlQueryForm, match.group(1).lower())


def init_ns_from_model(model_cls: type[BaseModel]) -> dict[str, Namespace]:
    """Build ``initNs`` for SPARQL from ``model_cls`` ``Rdf.prefixes``."""
    prefixes = get_rdf_config(model_cls).prefixes_dict
    return {prefix: Namespace(uri) for prefix, uri in prefixes.items()}


def init_bindings_from_model(
    instance: BaseModel,
    mapping: Mapping[str, str],
) -> dict[Variable, Node]:
    """Map SPARQL variable names to RDF terms from model field values."""
    bindings: dict[Variable, Node] = {}
    for var_name, field_name in mapping.items():
        if field_name not in type(instance).model_fields:
            raise ValueError(
                f"Unknown model field {field_name!r} in init_bindings mapping."
            )
        var = Variable(var_name.lstrip("?"))
        value = getattr(instance, field_name)
        bindings[var] = python_to_term(value)
    return bindings


def graph_from_construct_result(
    result: Result,
    graph_out: Graph | None = None,
) -> Graph:
    """Merge a CONSTRUCT/DESCRIBE ``Result`` graph into ``graph_out`` or a new graph."""
    if not _is_graph_result(result):
        raise TypeError(
            f"Expected a graph SPARQL result, got {result.type!r}. "
            "Use CONSTRUCT or DESCRIBE, or call select_models for SELECT."
        )
    target = graph_out or Graph()
    if result.graph is not None:
        for triple in result.graph:
            target.add(triple)
    return target


def run_sparql(
    graph: Graph,
    query: str | Query,
    *,
    model_cls: type[BaseModel] | None = None,
    initNs: Mapping[str, Any] | None = None,  # noqa: N803
    initBindings: Mapping[str, Node] | None = None,  # noqa: N803
    use_store_provided: bool = True,
    **kwargs: Any,
) -> Result:
    """Run ``graph.query`` with optional namespace binding from ``model_cls``."""
    resolved_init_ns = initNs
    if resolved_init_ns is None and model_cls is not None:
        resolved_init_ns = init_ns_from_model(model_cls)
    if model_cls is not None:
        bind_namespaces(graph, get_rdf_config(model_cls).prefixes_dict)
    return graph.query(
        query,
        initNs=resolved_init_ns,
        initBindings=initBindings,  # ty: ignore[invalid-argument-type]
        use_store_provided=use_store_provided,
        **kwargs,
    )


def ask(
    graph: Graph,
    query: str | Query,
    *,
    model_cls: type[BaseModel] | None = None,
    initNs: Mapping[str, Any] | None = None,  # noqa: N803
    initBindings: Mapping[str, Node] | None = None,  # noqa: N803
    use_store_provided: bool = True,
    **kwargs: Any,
) -> bool:
    """Execute an ASK query and return the boolean result."""
    result = run_sparql(
        graph,
        query,
        model_cls=model_cls,
        initNs=initNs,
        initBindings=initBindings,
        use_store_provided=use_store_provided,
        **kwargs,
    )
    if not _is_boolean_result(result):
        raise TypeError(f"Expected ASK (boolean) result, got {result.type!r}.")
    return bool(result.askAnswer)


def construct_models(
    model_cls: type[T],
    graph: Graph,
    query: str | Query,
    *,
    dispatch: bool = False,
    graph_out: Graph | None = None,
    type_uri: str | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
    initNs: Mapping[str, Any] | None = None,  # noqa: N803
    initBindings: Mapping[str, Node] | None = None,  # noqa: N803
    use_store_provided: bool = True,
    **kwargs: Any,
) -> list[T]:
    """Run CONSTRUCT/DESCRIBE and load models from the result graph."""
    result = run_sparql(
        graph,
        query,
        model_cls=model_cls,
        initNs=initNs,
        initBindings=initBindings,
        use_store_provided=use_store_provided,
        **kwargs,
    )
    merged = graph_from_construct_result(result, graph_out)
    bind_namespaces(merged, get_rdf_config(model_cls).prefixes_dict)
    if dispatch:
        from triplemodel.io.dispatch import all_from_graph_dispatch

        return cast(
            list[T],
            all_from_graph_dispatch(
                merged,
                validate_type=validate_type,
                on_duplicate=on_duplicate,
                resolver=resolver,
                registry=registry,
                de_skolemize=de_skolemize,
            ),
        )
    return model_cls.all_from_graph(  # ty: ignore[unresolved-attribute]
        merged,
        type_uri=type_uri,
        validate_type=validate_type,
        on_duplicate=on_duplicate,
        resolver=resolver,
        registry=registry,
        de_skolemize=de_skolemize,
    )


def _normalize_var_name(name: str) -> str:
    return name.lstrip("?")


def _binding_value(row: Mapping[Variable, Node], var_name: str) -> Node | None:
    key = Variable(_normalize_var_name(var_name))
    return row.get(key)


def _term_for_field(
    term: Node,
    field_info: Any,
    *,
    registry: LiteralRegistry,
) -> object:
    target = scalar_python_type(field_info)
    if target is not None:
        return term_to_python(term, target, registry=registry)
    members = union_member_types(field_info)
    if members:
        for member in members:
            try:
                return term_to_python(term, member, registry=registry)
            except (TypeError, ValueError):
                continue
    return term_to_python(term, registry=registry)


def _subject_id_from_uri(model_cls: type[BaseModel], uri: str) -> tuple[str, object]:
    cfg = get_rdf_config(model_cls)
    id_field = cfg.id_field
    if not id_field:
        raise ValueError(
            f"{model_cls.__name__} has no Rdf.id_field; pass subject_var only when "
            "id_field is configured, or omit subject_var."
        )
    if id_field_is_iri_id(model_cls, id_field):
        return id_field, uri
    segment = id_from_subject_uri(cfg.namespace, uri)
    if segment is not None:
        return id_field, segment
    return id_field, uri


def _default_field_map(result: Result) -> dict[str, str]:
    vars_ = result.vars or []
    return {
        _normalize_var_name(str(var)): _normalize_var_name(str(var)) for var in vars_
    }


def select_models(
    model_cls: type[T],
    graph: Graph,
    query: str | Query,
    *,
    field_map: Mapping[str, str] | None = None,
    subject_var: str | None = None,
    hydrate: bool = False,
    type_uri: str | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
    initNs: Mapping[str, Any] | None = None,  # noqa: N803
    initBindings: Mapping[str, Node] | None = None,  # noqa: N803
    use_store_provided: bool = True,
    **kwargs: Any,
) -> list[T]:
    """Run SELECT and return model instances from result bindings or hydration."""
    if hydrate:
        if not subject_var:
            raise ValueError("select_models(hydrate=True) requires subject_var=.")
        return _select_models_hydrate(
            model_cls,
            graph,
            query,
            subject_var=subject_var,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
            initNs=initNs,
            initBindings=initBindings,
            use_store_provided=use_store_provided,
            **kwargs,
        )
    return _select_models_projection(
        model_cls,
        graph,
        query,
        field_map=field_map,
        subject_var=subject_var,
        initNs=initNs,
        initBindings=initBindings,
        use_store_provided=use_store_provided,
        registry=registry,
        **kwargs,
    )


def _select_models_hydrate(
    model_cls: type[T],
    graph: Graph,
    query: str | Query,
    *,
    subject_var: str,
    validate_type: bool,
    on_duplicate: OnDuplicate,
    resolver: PredicateResolverProtocol | None,
    registry: LiteralRegistry,
    de_skolemize: bool | None,
    initNs: Mapping[str, Any] | None,
    initBindings: Mapping[str, Node] | None,
    use_store_provided: bool,
    **kwargs: Any,
) -> list[T]:
    result = run_sparql(
        graph,
        query,
        model_cls=model_cls,
        initNs=initNs,
        initBindings=initBindings,
        use_store_provided=use_store_provided,
        **kwargs,
    )
    if not _is_bindings_result(result):
        raise TypeError(f"Expected SELECT (bindings) result, got {result.type!r}.")
    instances: list[T] = []
    seen: set[str] = set()
    for row in result:
        term = _binding_value(cast("Mapping[Variable, Node]", row), subject_var)
        if term is None:
            continue
        uri = str(term)
        if uri in seen:
            continue
        seen.add(uri)
        instances.append(
            graph_to_model(
                graph,
                model_cls,
                uri,
                validate_type=validate_type,
                on_duplicate=on_duplicate,
                resolver=resolver,
                registry=registry,
                de_skolemize=de_skolemize,
            )
        )
    return instances


def _select_models_projection(
    model_cls: type[T],
    graph: Graph,
    query: str | Query,
    *,
    field_map: Mapping[str, str] | None,
    subject_var: str | None,
    initNs: Mapping[str, Any] | None,
    initBindings: Mapping[str, Node] | None,
    use_store_provided: bool,
    registry: LiteralRegistry,
    **kwargs: Any,
) -> list[T]:
    result = run_sparql(
        graph,
        query,
        model_cls=model_cls,
        initNs=initNs,
        initBindings=initBindings,
        use_store_provided=use_store_provided,
        **kwargs,
    )
    if not _is_bindings_result(result):
        raise TypeError(f"Expected SELECT (bindings) result, got {result.type!r}.")
    mapping = dict(field_map) if field_map is not None else _default_field_map(result)
    for var_name, field_name in mapping.items():
        if field_name not in model_cls.model_fields:
            raise ValueError(
                f"Unknown model field {field_name!r} in field_map "
                f"(SPARQL variable {var_name!r})."
            )
    instances: list[T] = []
    subject_key = _normalize_var_name(subject_var) if subject_var else None
    for row in result:
        row_map = cast("Mapping[Variable, Node]", row)
        data: dict[str, object] = {}
        if subject_key and subject_key not in mapping:
            term = _binding_value(row_map, subject_key)
            if term is not None:
                id_field, id_value = _subject_id_from_uri(model_cls, str(term))
                data[id_field] = id_value
        for var_name, field_name in mapping.items():
            term = _binding_value(row_map, var_name)
            if term is None:
                continue
            field_info = model_cls.model_fields[field_name]
            data[field_name] = _term_for_field(term, field_info, registry=registry)
        instances.append(model_cls.model_validate(data))
    return instances


def apply_update(
    graph: Graph,
    update: str,
    *,
    model_cls: type[BaseModel] | None = None,
    initNs: Mapping[str, Any] | None = None,  # noqa: N803
    initBindings: Mapping[str, Node] | None = None,  # noqa: N803
    use_store_provided: bool = True,
    **kwargs: Any,
) -> None:
    """Apply a SPARQL UPDATE to ``graph`` (in-memory models may be stale afterward)."""
    resolved_init_ns = initNs
    if resolved_init_ns is None and model_cls is not None:
        resolved_init_ns = init_ns_from_model(model_cls)
    if model_cls is not None:
        bind_namespaces(graph, get_rdf_config(model_cls).prefixes_dict)
    graph.update(
        update,
        initNs=resolved_init_ns,
        initBindings=initBindings,  # ty: ignore[invalid-argument-type]
        use_store_provided=use_store_provided,
        **kwargs,
    )


@dataclass(frozen=True)
class PreparedModelQuery:
    """Prepared SPARQL query with namespaces from a model's ``Rdf.prefixes``."""

    model_cls: type[BaseModel]
    prepared: Query

    def execute(
        self,
        graph: Graph,
        *,
        initBindings: Mapping[str, Node] | None = None,  # noqa: N803
        use_store_provided: bool = True,
        **kwargs: Any,
    ) -> Result:
        """Run the prepared query on ``graph``."""
        return run_sparql(
            graph,
            self.prepared,
            model_cls=self.model_cls,
            initBindings=initBindings,
            use_store_provided=use_store_provided,
            **kwargs,
        )

    def as_result(self, graph: Graph, **kwargs: Any) -> Result:
        """Alias for :meth:`execute`."""
        return self.execute(graph, **kwargs)


def prepare_model_query(model_cls: type[BaseModel], query: str) -> PreparedModelQuery:
    """Prepare ``query`` with ``initNs`` from ``model_cls`` ``Rdf.prefixes``."""
    prepared = prepareQuery(query, initNs=init_ns_from_model(model_cls))
    return PreparedModelQuery(model_cls=model_cls, prepared=prepared)


def open_sparql_graph(endpoint: str, *, read_only: bool = True) -> Graph:
    """Open a remote SPARQL endpoint as an rdflib ``Graph``."""
    if read_only:
        from rdflib.plugins.stores.sparqlstore import SPARQLStore

        return Graph(store=SPARQLStore(endpoint))
    from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

    return Graph(store=SPARQLUpdateStore(endpoint))


@overload
def load_sparql(
    model_cls: type[T],
    endpoint: str,
    query: str | Query,
    *,
    query_form: SparqlQueryForm,
    read_only: bool = True,
    dispatch: bool = False,
    **kwargs: Any,
) -> list[T]: ...


@overload
def load_sparql(
    model_cls: type[T],
    endpoint: str,
    query: str | Query,
    *,
    read_only: bool = True,
    dispatch: bool = False,
    **kwargs: Any,
) -> list[T]: ...


def load_sparql(
    model_cls: type[T],
    endpoint: str,
    query: str | Query,
    *,
    query_form: SparqlQueryForm | None = None,
    read_only: bool = True,
    dispatch: bool = False,
    type_uri: str | None = None,
    validate_type: bool = True,
    on_duplicate: OnDuplicate = "warn",
    resolver: PredicateResolverProtocol | None = None,
    registry: LiteralRegistry = default_registry,
    de_skolemize: bool | None = None,
    initNs: Mapping[str, Any] | None = None,  # noqa: N803
    initBindings: Mapping[str, Node] | None = None,  # noqa: N803
    use_store_provided: bool = True,
    **kwargs: Any,
) -> list[T]:
    """Query a remote SPARQL endpoint and return model instances."""
    form = query_form
    if form is None:
        if isinstance(query, str):
            form = detect_query_form(query)
        else:
            form = "unknown"
    if form == "ask":
        raise TypeError(
            "ASK queries do not return models; use ask(open_sparql_graph(endpoint), query)."
        )
    graph = open_sparql_graph(endpoint, read_only=read_only)
    bind_namespaces(graph, get_rdf_config(model_cls).prefixes_dict)
    if form in ("construct", "describe"):
        return construct_models(
            model_cls,
            graph,
            query,
            dispatch=dispatch,
            type_uri=type_uri,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
            initNs=initNs,
            initBindings=initBindings,
            use_store_provided=use_store_provided,
            **kwargs,
        )
    if form == "select":
        return select_models(
            model_cls,
            graph,
            query,
            validate_type=validate_type,
            on_duplicate=on_duplicate,
            resolver=resolver,
            registry=registry,
            de_skolemize=de_skolemize,
            initNs=initNs,
            initBindings=initBindings,
            use_store_provided=use_store_provided,
            **kwargs,
        )
    raise ValueError(
        f"Cannot load models from SPARQL query form {form!r}; "
        "use CONSTRUCT, DESCRIBE, or SELECT."
    )


__all__ = [
    "PreparedModelQuery",
    "SparqlQueryForm",
    "SparqlResultKind",
    "apply_update",
    "ask",
    "construct_models",
    "detect_query_form",
    "graph_from_construct_result",
    "init_bindings_from_model",
    "init_ns_from_model",
    "load_sparql",
    "open_sparql_graph",
    "prepare_model_query",
    "run_sparql",
    "select_models",
]
