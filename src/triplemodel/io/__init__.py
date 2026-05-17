"""Graph I/O: export, import, sync, and helpers."""

from triplemodel.io.discovery import discover_subject_uris
from triplemodel.io.export import model_to_triples
from triplemodel.io.graph import model_to_graph, models_to_graph, write_model_add
from triplemodel.io.import_ import (
    OnDuplicate,
    graph_to_model,
    graph_to_models,
    import_field_value,
)
from triplemodel.io.ops import (
    graph_set,
    graph_set_many,
    graph_value,
    merge_graphs,
    objects_for_field,
)
from triplemodel.io.sync import sync_to_graph
from triplemodel.io.files import (
    dump_graph,
    dump_model,
    fetch_url,
    infer_format,
    load_models,
    parse_into_graph,
    parse_url_into_graph,
)
from triplemodel.io.dispatch import (
    all_from_graph_dispatch,
    graph_to_model_dispatch,
)

__all__ = [
    "OnDuplicate",
    "all_from_graph_dispatch",
    "discover_subject_uris",
    "dump_graph",
    "dump_model",
    "fetch_url",
    "graph_to_model_dispatch",
    "infer_format",
    "load_models",
    "parse_into_graph",
    "parse_url_into_graph",
    "graph_set",
    "graph_set_many",
    "graph_to_model",
    "graph_to_models",
    "graph_value",
    "import_field_value",
    "merge_graphs",
    "model_to_graph",
    "model_to_triples",
    "models_to_graph",
    "objects_for_field",
    "sync_to_graph",
    "write_model_add",
]
