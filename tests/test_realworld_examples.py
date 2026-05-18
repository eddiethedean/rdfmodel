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

    bundles = load_models(
        REALWORLD / "data" / "nobel_laureates_1901.ttl", Laureate, NobelPrize
    )
    assert len(bundles[Laureate]) >= 1
    assert len(bundles[NobelPrize]) >= 1
    roentgen = next(p for p in bundles[Laureate] if "Röntgen" in p.name)
    physics = next(p for p in bundles[NobelPrize] if p.slug == "Physics/1901")
    assert physics.year == "1901"
    assert roentgen.gender is not None


def test_dcat_load_models_api(realworld_path: None) -> None:
    sys.path.insert(0, str(REALWORLD))
    from dcat_data_catalog import (  # noqa: E402  # ty: ignore[unresolved-import]
        DataCatalog,
        Dataset,
        Distribution,
    )
    from triplemodel import load_models  # noqa: E402

    bundles = load_models(
        REALWORLD / "data" / "dcat_nobel_catalog.ttl",
        DataCatalog,
        Dataset,
        Distribution,
    )
    assert len(bundles[DataCatalog]) >= 1
    assert len(bundles[Dataset]) >= 1
    assert len(bundles[Distribution]) >= 1
    assert any("nobelprize.org/sparql" in d.access_url for d in bundles[Distribution])


def test_wikidata_instance_of_and_ref_field(realworld_path: None) -> None:
    sys.path.insert(0, str(REALWORLD))
    from wikidata_capitals import CapitalCity, load_graph  # noqa: E402  # ty: ignore[unresolved-import]
    from triplemodel import hydrate_refs  # noqa: E402

    graph = load_graph(
        source=REALWORLD / "data" / "wikidata_capitals.ttl",
        bind_prefixes=CapitalCity.Rdf.prefixes,
    )
    cities = hydrate_refs(
        CapitalCity.all_from_graph(graph, validate_type=False),
        graph,
        "country",
    )
    assert len(cities) == 2
    paris = next(c for c in cities if c.qid.endswith("Q90"))
    london = next(c for c in cities if c.qid.endswith("Q84"))
    assert paris.country.label_en == "France"
    assert london.country.label_en == "United Kingdom"
    assert paris.country.qid.endswith("Q142")
    assert london.country.qid.endswith("Q145")


def test_schema_org_gyear_from_bundled_ttl(realworld_path: None) -> None:
    sys.path.insert(0, str(REALWORLD))
    from schema_org_ngos import NgoOrganization  # noqa: E402  # ty: ignore[unresolved-import]

    ngos = NgoOrganization.parse_file(REALWORLD / "data" / "schema_org_ngos.ttl")
    wwf = next(o for o in ngos if o.slug == "wwf")
    assert wwf.founding_year == 1961


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
