# Examples

Runnable scripts live in the repository [`examples/`](https://github.com/eddiethedean/triplemodel/tree/main/examples) directory on GitHub.

Guide and README snippets that show **Output** blocks are driven by [`examples/doc/`](https://github.com/eddiethedean/triplemodel/tree/main/examples/doc) (`snippets/` + checked-in `outputs/`). Regenerate with `python examples/doc/regenerate_outputs.py` from the repo root (`PYTHONPATH=src:.`).

## FOAF Person (0.2 exit criteria)

[`examples/foaf_person_02.py`](https://github.com/eddiethedean/triplemodel/blob/main/examples/foaf_person_02.py) demonstrates **0.2** semantics (before the 0.3 `list`/`set` split):

- Multiple `foaf:nick` objects per predicate (`list[str]` in 0.2 — use `set[str]` for that pattern on **0.3**)
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

## 0.3 exit criteria

[`examples/exit_criteria_03.py`](https://github.com/eddiethedean/triplemodel/blob/main/examples/exit_criteria_03.py) demonstrates:

- Dublin Core `title` with `LangString`
- Blank-node `Address` embed
- Ordered `nick` as `rdf:List` (`list[str]`)

```bash
PYTHONPATH=src python examples/exit_criteria_03.py
```

## README examples

[`examples/readme_examples.py`](https://github.com/eddiethedean/triplemodel/blob/main/examples/readme_examples.py) exercises snippets from the project README (batch export, encoded ids, etc.).

```bash
PYTHONPATH=src python examples/readme_examples.py
```
