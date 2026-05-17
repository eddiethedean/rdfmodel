# Releasing TripleModel

## 0.2.0 release readiness (repo)

The following should be satisfied on `main` before tagging:

- Version `0.2.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md` (no open `[Unreleased]` entries except an empty stub)
- `src/triplemodel/py.typed` present; wheel includes `triplemodel/py.typed` (`twine check` passes)
- CI green: `pytest` (100% coverage), `python -m build`, `ruff format --check`, `ruff check`, `ty check` (Python 3.10–3.13)

**Remaining manual steps:** tag `v0.2.0`, GitHub release, confirm PyPI publish. ROADMAP **0.2.0** is marked **Released (alpha)**.

## Pre-release checklist

- [ ] `version` `0.2.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [ ] CI on `main`: `pytest` (100% coverage), `ruff format --check`, `ruff check`, `ty check`, `python -m build` (Python 3.10 / 3.11 / 3.12 / 3.13)
- [ ] Local: `ruff format src tests`, `ty check src tests`, `PYTHONPATH=src python examples/readme_examples.py`
- [ ] `python -m build` and `twine check dist/*` pass
- [ ] Create and push git tag `v0.2.0` (triggers Release workflow: build + PyPI publish)
- [ ] GitHub release from tag

## Publish to PyPI

### GitHub Actions (default)

1. In the repo **Settings → Secrets and variables → Actions**, add **`PYPI_API_TOKEN`**: a PyPI [API token](https://pypi.org/manage/account/token/) scoped to the `triplemodel` project (or the whole account for first release).
2. Push an annotated tag `v*` (e.g. `v0.2.0`). The [Release workflow](.github/workflows/release.yml) runs `pytest`, `python -m build`, `twine check`, uploads `dist/` as an artifact, then publishes with [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish).

### Manual fallback

```bash
python -m pip install build twine
python -m build
twine check dist/*
twine upload dist/*   # uses ~/.pypirc or PyPI token
```

## Read the Docs

After pushing to `main`:

1. Import the project at [readthedocs.org](https://readthedocs.org/) (suggested slug: **triplemodel**).
2. Point it at `eddiethedean/triplemodel`; config file `.readthedocs.yaml` is used automatically.
3. Confirm the build is green; site URL: `https://triplemodel.readthedocs.io/`.
4. Optional: add the docs badge to `README.md` and set PyPI **Project-URL: Documentation** (already `https://triplemodel.readthedocs.io/` in `pyproject.toml`).

Local check: `pip install -e ".[docs]" && make -C docs html` (or `sphinx-build -b html docs docs/_build/html -W`).

## Git tag and GitHub release

```bash
git tag -a v0.2.0 -m "Release 0.2.0"
git push origin v0.2.0
```

Create a GitHub release from the tag and attach the sdist/wheel if desired.
