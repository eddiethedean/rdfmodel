"""Packaging and PEP 561 markers."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from importlib.resources import files
from pathlib import Path


def test_py_typed_marker_in_source() -> None:
    path = Path(__file__).resolve().parents[1] / "src" / "triplemodel" / "py.typed"
    assert path.is_file()


def test_py_typed_marker_in_installed_package() -> None:
    pkg = files("triplemodel")
    assert (pkg / "py.typed").is_file()


def test_wheel_contains_py_typed() -> None:
    root = Path(__file__).resolve().parents[1]
    wheels = list((root / "dist").glob("triplemodel-*.whl"))
    if not wheels:
        subprocess.run(
            [sys.executable, "-m", "build", str(root)],
            check=True,
            capture_output=True,
        )
        wheels = list((root / "dist").glob("triplemodel-*.whl"))
    assert wheels, "expected a built wheel after python -m build"
    wheel = max(wheels, key=lambda p: p.stat().st_mtime)
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    assert any(n.endswith("triplemodel/py.typed") for n in names)


def test_sparql_helpers_importable_from_top_level() -> None:
    """Names documented in guides/13-sparql-and-endpoints.md."""
    import triplemodel

    for name in (
        "ask",
        "apply_update",
        "construct_models",
        "select_models",
        "load_sparql",
        "open_sparql_graph",
        "prepare_model_query",
        "init_bindings_from_model",
        "detect_query_form",
        "run_sparql",
        "init_ns_from_model",
        "graph_from_construct_result",
    ):
        assert name in triplemodel.__all__
        assert getattr(triplemodel, name) is not None


def test_graph_algorithms_helpers_importable_from_top_level() -> None:
    """Names documented in guides/14-graph-algorithms-and-rdfs.md."""
    import triplemodel

    for name in (
        "graphs_equal",
        "graph_diff",
        "model_diff",
        "cbd_graph",
        "cbd_model",
        "hydrate_refs",
        "model_join",
        "resolve_model_class_with_rdfs",
        "subject_type_closure",
        "subclass_uris",
        "transitive_objects",
        "transitive_subjects",
        "VocabularyRegistry",
        "Transitive",
    ):
        assert name in triplemodel.__all__
        assert getattr(triplemodel, name) is not None


def test_dataset_helpers_importable_from_top_level() -> None:
    """Names documented in guides/12-datasets-and-named-graphs.md."""
    import triplemodel

    for name in (
        "all_from_dataset",
        "graph_to_model_from_dataset",
        "graph_to_models_from_dataset",
        "iter_model_quads",
        "quads_in_context",
    ):
        assert name in triplemodel.__all__
        assert getattr(triplemodel, name) is not None
