"""Run real-world example scripts against bundled RDF data."""

from __future__ import annotations

import runpy
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

REALWORLD = Path(__file__).resolve().parents[1] / "examples" / "realworld"


@pytest.fixture
def realworld_path() -> Iterator[None]:
    root = str(REALWORLD)
    if root not in sys.path:
        sys.path.insert(0, root)
    yield
    if root in sys.path:
        sys.path.remove(root)


@pytest.mark.parametrize(
    "script",
    [
        "nobel_laureates.py",
        "dcat_data_catalog.py",
        "wikidata_capitals.py",
        "schema_org_ngos.py",
    ],
)
def test_realworld_example_runs(script: str, realworld_path: None) -> None:
    runpy.run_path(str(REALWORLD / script), run_name="__main__")


def test_nobel_load_models_api(realworld_path: None) -> None:
    sys.path.insert(0, str(REALWORLD))
    from nobel_laureates import Laureate, NobelPrize  # noqa: E402  # ty: ignore[unresolved-import]
    from triplemodel import load_models  # noqa: E402

    bundles = load_models(REALWORLD / "data" / "nobel_laureates_1901.ttl", Laureate, NobelPrize)
    assert len(bundles[Laureate]) >= 1
    assert len(bundles[NobelPrize]) >= 1


def test_bundled_data_files_exist() -> None:
    data = REALWORLD / "data"
    names = [
        "nobel_laureates_1901.ttl",
        "dcat_nobel_catalog.ttl",
        "wikidata_capitals.ttl",
        "schema_org_ngos.ttl",
    ]
    for name in names:
        assert (data / name).is_file()
