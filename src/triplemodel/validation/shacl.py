"""SHACL validation via optional pyshacl dependency."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib import Graph


def validate_graph(
    data_graph: Graph,
    shapes: Graph | str | Path,
    **pyshacl_kwargs: Any,
) -> None:
    """Validate ``data_graph`` against SHACL shapes; raise ``ValueError`` on failure."""
    try:
        import pyshacl
    except ImportError as exc:
        raise ImportError(
            "SHACL validation requires pyshacl. Install with: pip install triplemodel[shacl]"
        ) from exc

    if isinstance(shapes, Path):
        shapes_graph = Graph().parse(str(shapes))
    elif isinstance(shapes, str):
        path = Path(shapes)
        if path.is_file():
            shapes_graph = Graph().parse(str(path))
        else:
            shapes_graph = Graph().parse(data=shapes, format="turtle")
    else:
        shapes_graph = shapes

    conforms, report_graph, report_text = pyshacl.validate(
        data_graph,
        shacl_graph=shapes_graph,
        **pyshacl_kwargs,
    )
    if not conforms:
        raise ValueError(f"SHACL validation failed:\n{report_text}")
