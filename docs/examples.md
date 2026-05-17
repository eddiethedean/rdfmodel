# Examples

Runnable scripts live in the repository [`examples/`](https://github.com/eddiethedean/triplemodel/tree/main/examples) directory on GitHub.

## FOAF Person (0.2 exit criteria)

[`examples/foaf_person_02.py`](https://github.com/eddiethedean/triplemodel/blob/main/examples/foaf_person_02.py) demonstrates:

- Multi-value `foaf:nick` (`list[str]`)
- Nested `Mailbox` embedded with `Rdf.embed = "iri"`
- `Rdf.prefixes` and Turtle `PREFIX foaf:`
- Clearing `foaf:age` with `sync_to_graph(..., mode="replace")`

```bash
pip install triplemodel
git clone https://github.com/eddiethedean/triplemodel.git
cd triplemodel
PYTHONPATH=src python examples/foaf_person_02.py
```

```{literalinclude} ../examples/foaf_person_02.py
:language: python
:caption: examples/foaf_person_02.py
```

## README examples

[`examples/readme_examples.py`](https://github.com/eddiethedean/triplemodel/blob/main/examples/readme_examples.py) exercises snippets from the project README (batch export, encoded ids, etc.).

```bash
PYTHONPATH=src python examples/readme_examples.py
```
