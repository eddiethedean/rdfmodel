# Examples

Runnable scripts live in the repository [`examples/`](https://github.com/eddiethedean/triplemodel/tree/main/examples) directory on GitHub.

Guide and README snippets that show **Output** blocks are driven by [`examples/doc/`](https://github.com/eddiethedean/triplemodel/tree/main/examples/doc) (`snippets/` + checked-in `outputs/`). Regenerate with `python examples/doc/regenerate_outputs.py` from the repo root (`PYTHONPATH=src:.`).

## Full walkthrough (`exit_criteria_03.py`)

[`examples/exit_criteria_03.py`](https://github.com/eddiethedean/triplemodel/blob/main/examples/exit_criteria_03.py) demonstrates:

- Dublin Core `title` with `LangString`
- Blank-node `Address` embed
- Ordered `nick` as `rdf:List` (`list[str]`)
- `sync_to_graph(..., mode="replace")` after editing a list field

```bash
pip install triplemodel
git clone https://github.com/eddiethedean/triplemodel.git
cd triplemodel
PYTHONPATH=src python examples/exit_criteria_03.py
```

```{literalinclude} ../examples/exit_criteria_03.py
:language: python
:caption: examples/exit_criteria_03.py
```

## README examples

[`examples/readme_examples.py`](https://github.com/eddiethedean/triplemodel/blob/main/examples/readme_examples.py) exercises snippets from the project README (quick start, batch export, encoded subject ids, etc.).

```bash
PYTHONPATH=src python examples/readme_examples.py
```

## Nested model with sync (`foaf_person_02.py`)

[`examples/foaf_person_02.py`](https://github.com/eddiethedean/triplemodel/blob/main/examples/foaf_person_02.py) shows nested `Mailbox` (IRI embed), `Rdf.prefixes`, multiple `foaf:nick` values via **`set[str]`**, and clearing `foaf:age` with sync.

```bash
PYTHONPATH=src python examples/foaf_person_02.py
```

## Real-world data (`examples/realworld/`)

Bundled RDF from public sources (Nobel Prize linked data, DCAT catalogs, Wikidata, Schema.org). Each script maps a **concrete integration problem**—see [`examples/realworld/README.md`](https://github.com/eddiethedean/triplemodel/blob/main/examples/realworld/README.md) and [`DATA_SOURCES.md`](https://github.com/eddiethedean/triplemodel/blob/main/examples/realworld/DATA_SOURCES.md).

```bash
PYTHONPATH=src python examples/realworld/nobel_laureates.py
PYTHONPATH=src python examples/realworld/dcat_data_catalog.py
PYTHONPATH=src python examples/realworld/wikidata_capitals.py
PYTHONPATH=src python examples/realworld/schema_org_ngos.py
```
