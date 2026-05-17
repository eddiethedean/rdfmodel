# Releasing TripleModel

## 0.1.0 release readiness (repo)

The following are satisfied on `main` before tagging:

- Version `0.1.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md` (no open `[Unreleased]` entries)
- `src/triplemodel/py.typed` present; wheel includes `triplemodel/py.typed` (`twine check` passes)
- CI green: `pytest` (100% coverage), `python -m build`, `ruff format --check`, `ruff check`, `ty check` (Python 3.10–3.13)

**Remaining manual steps:** tag `v0.1.0`, `twine upload`, GitHub release, then set ROADMAP **0.1.0** status to **Released (alpha)**.

## Pre-release checklist

- [x] `version` `0.1.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] CI on `main`: `pytest` (100% coverage), `ruff format --check`, `ruff check`, `ty check`, `python -m build` (Python 3.10 / 3.11 / 3.12 / 3.13)
- [x] Local: `ruff format`, `ty check src tests`, `PYTHONPATH=src python examples/readme_examples.py`
- [x] `python -m build` and `twine check dist/*` pass
- [x] PyPI name `triplemodel` available (not yet published)
- [x] GitHub repo `eddiethedean/triplemodel` (renamed from `tripletyped`)
- [ ] Create and push git tag `v0.1.0` (triggers Release workflow build)
- [ ] `twine upload dist/*`
- [ ] GitHub release from tag; set `docs/ROADMAP.md` **0.1.0** to **Released (alpha)**

## Publish to PyPI

```bash
python -m pip install build twine
python -m build
twine check dist/*
twine upload dist/*   # uses ~/.pypirc or PyPI token
```

## Git tag and GitHub release

```bash
git tag -a v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0
```

Create a GitHub release from the tag and attach the sdist/wheel if desired. After publish, set `docs/ROADMAP.md` **0.1.0** status to **Released (alpha)**.
