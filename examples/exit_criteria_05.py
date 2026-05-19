"""0.5.0 exit criteria: two model types in different named graphs round-trip via TriG."""

from __future__ import annotations

from pathlib import Path
import tempfile

from triplemodel import (
    TripleModel,
    load_models_from_dataset,
    models_to_dataset,
    rdf_field,
)
from triplemodel.io.dataset import dump_dataset, parse_into_dataset
from triplemodel.vocab import FOAF

PEOPLE_GRAPH = "http://example.org/graph/people"
CATALOG_GRAPH = "http://example.org/graph/catalog"
DCAT = "http://www.w3.org/ns/dcat#"


class Person(TripleModel):
    class Rdf:
        namespace = "http://example.org/people/"
        type_uri = f"{FOAF}Person"
        id_field = "slug"
        graph_iri = PEOPLE_GRAPH
        prefixes = {"foaf": str(FOAF)}

    slug: str
    name: str = rdf_field("foaf:name")


class Catalog(TripleModel):
    class Rdf:
        namespace = "http://example.org/catalog/"
        type_uri = f"{DCAT}Catalog"
        id_field = "slug"
        graph_iri = CATALOG_GRAPH
        prefixes = {"dcat": str(DCAT)}

    slug: str
    title: str = rdf_field(f"{DCAT}title")


def main() -> None:
    alice = Person(slug="alice", name="Alice")
    cat = Catalog(slug="nobel", title="Nobel catalog")
    ds = models_to_dataset([alice, cat])
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "data.trig"
        dump_dataset(ds, path, format="trig")
        file_ds = parse_into_dataset(path)
        loaded = load_models_from_dataset(file_ds, Person, Catalog)
        assert len(loaded[Person]) == 1
        assert len(loaded[Catalog]) == 1
        assert loaded[Person][0].name == "Alice"
        assert loaded[Catalog][0].title == "Nobel catalog"
        assert loaded[Person][0].slug == "alice"
        assert loaded[Catalog][0].slug == "nobel"
    print("0.5.0 named-graph TriG round-trip OK")


if __name__ == "__main__":
    main()
