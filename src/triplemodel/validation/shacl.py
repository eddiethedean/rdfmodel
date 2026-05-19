"""SHACL validation via optional pyshacl dependency (rdflib bridge)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from triplemodel.store import RdfGraph as Graph


def _to_rdflib_graph(graph: Graph) -> Any:
    from rdflib import BNode, Graph as RdfLibGraph, Literal, URIRef

    out = RdfLibGraph()
    for s, p, o in graph:

        def term(t: Any) -> Any:
            from pyoxigraph import BlankNode, Literal as OxLiteral, NamedNode

            if isinstance(t, NamedNode):
                return URIRef(str(t.value))
            if isinstance(t, BlankNode):
                return BNode(str(t))
            if isinstance(t, OxLiteral):
                if t.language:
                    return Literal(str(t.value), lang=t.language)
                if t.datatype is not None:
                    return Literal(str(t.value), datatype=URIRef(str(t.datatype.value)))
                return Literal(str(t.value))  # pragma: no cover
            return t  # pragma: no cover

        out.add((term(s), term(p), term(o)))
    return out


def validate_graph(
    data_graph: Graph,
    shapes: Graph | str | Path | Any,
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
        shapes_ox = Graph()
        shapes_ox.parse(str(shapes), format="turtle")
        shapes_graph = _to_rdflib_graph(shapes_ox)
    elif isinstance(shapes, str):
        path = Path(shapes)
        if path.is_file():
            shapes_ox = Graph()
            shapes_ox.parse(str(path), format="turtle")
            shapes_graph = _to_rdflib_graph(shapes_ox)
        else:
            shapes_ox = Graph()
            shapes_ox.parse(data=shapes, format="turtle")
            shapes_graph = _to_rdflib_graph(shapes_ox)
    else:
        try:
            from rdflib import Graph as RdflibGraph

            if isinstance(shapes, RdflibGraph):
                shapes_graph = shapes
            else:
                shapes_graph = _to_rdflib_graph(shapes)
        except ImportError:  # pragma: no cover
            shapes_graph = _to_rdflib_graph(shapes)

    data_rdf = _to_rdflib_graph(data_graph)
    conforms, report_graph, report_text = pyshacl.validate(
        data_rdf,
        shacl_graph=shapes_graph,
        **pyshacl_kwargs,
    )
    _ = report_graph
    if not conforms:
        raise ValueError(f"SHACL validation failed:\n{report_text}")
