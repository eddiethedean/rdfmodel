# TripleModel documentation sources

This directory is the **Sphinx** source root for [Read the Docs](https://triplemodel.readthedocs.io/).

| Path | Role |
|------|------|
| `conf.py` | Sphinx configuration (MyST, autodoc, RTD theme) |
| `index.md` | Documentation home and navigation toctrees |
| `guides/` | User guides (Markdown) |
| `api/` | API reference (reStructuredText + autodoc) |
| `Makefile` | Local `make html` builds |

## Build locally

```bash
pip install -e ".[docs]"
make -C docs html
# open docs/_build/html/index.html
```

Equivalent:

```bash
sphinx-build -b html docs docs/_build/html -W
```

## Read the Docs

1. Sign in at [readthedocs.org](https://readthedocs.org/) and **Import a project** for `eddiethedean/triplemodel`.
2. Use the default config file `.readthedocs.yaml` at the repository root.
3. Set the **Documentation** URL in PyPI / GitHub to `https://triplemodel.readthedocs.io/`.

Optional: enable **PDF/Epub** builds (already listed under `formats:` in `.readthedocs.yaml`).

## GitHub vs RTD

- **RTD / Sphinx** uses `index.md` and `guides/index.md` for navigation.
- The table in `guides/README.md` remains for browsing on GitHub; prefer `guides/index.md` when editing toctrees.
