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

The project disables the third-party **`pytest_green_light`** plugin in `pyproject.toml` (it injects an async autouse fixture into every test). If you still see hundreds of `ensure_greenlet_context` warnings, uninstall that package from your environment or run `pytest` from the repo root so project `addopts` apply.

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

Open `http://localhost:8000`. User guides are Markdown under `docs/guides/`; API reference is generated from docstrings via Sphinx autodoc.

CI runs **HTML only** on each push/PR (fast). **Linkcheck** runs weekly and on demand via the Docs workflow (`workflow_dispatch`); run `sphinx-build -b linkcheck docs docs/_build/linkcheck -W` locally before large doc edits.

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
