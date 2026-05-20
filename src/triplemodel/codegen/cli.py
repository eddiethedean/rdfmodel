"""CLI entry point for OWL/RDFS stub codegen."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from triplemodel.codegen.emit import generate_models_from_graph
from triplemodel.codegen.parse import ontology_graph


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="triplemodel-codegen",
        description="Generate experimental TripleModel stubs from OWL/RDFS.",
    )
    parser.add_argument("ontology", type=Path, help="Path to ontology file (TTL, etc.)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write Python module to this path (default: stdout)",
    )
    parser.add_argument(
        "--format",
        default=None,
        help="pyoxigraph parse format (inferred from suffix if omitted)",
    )
    args = parser.parse_args(argv)
    graph = ontology_graph(args.ontology, format=args.format)
    source = generate_models_from_graph(graph)
    if args.output:
        args.output.write_text(source, encoding="utf-8")
    else:
        sys.stdout.write(source)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
