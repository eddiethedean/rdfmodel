# Releasing TripleModel

## Pre-release checklist

- [x] `version` `0.1.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] CI on `main`: `pytest` (62 tests, 100% coverage), `ruff check` (Python 3.10 / 3.12 / 3.13)
- [x] Local: `ruff format`, `ty check src tests`, `PYTHONPATH=src python examples/readme_examples.py`
- [x] `python -m build` and `twine check dist/*` pass
- [x] PyPI name `triplemodel` available (not yet published)
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
