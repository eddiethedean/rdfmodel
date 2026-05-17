# Contributing

Thank you for improving TripleModel. This project targets **100% test coverage** on `src/triplemodel`, strict **ruff** formatting, and **`ty check`** on `src` and `tests`.

## Development setup

```bash
git clone https://github.com/eddiethedean/triplemodel.git
cd triplemodel
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
```

## Checks (match CI)

```bash
pytest
ruff format --check src tests
ruff check src tests
ty check src tests
python -m build
```

## Documentation

Build docs locally (same as Read the Docs):

```bash
sphinx-build -b html docs docs/_build/html -W
python -m http.server -d docs/_build/html 8000
```

Open http://localhost:8000. User guides are Markdown under `docs/guides/`; API reference is generated from docstrings via Sphinx autodoc.

### Runnable examples in docs

Snippets that show **Output** live under `examples/doc/snippets/` with checked-in stdout in `examples/doc/outputs/`. After changing a snippet:

```bash
PYTHONPATH=src:. python examples/doc/regenerate_outputs.py
pytest tests/test_doc_examples.py
```

## Pull requests

- Keep changes focused; match existing style in `src/triplemodel/`.
- Add or update tests for behaviour changes.
- Update `CHANGELOG.md` under `[Unreleased]` when user-visible behaviour changes.
- Update user guides under `docs/guides/` when the public workflow changes.

Release process: see {doc}`releasing`.
