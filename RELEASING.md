# Releasing RDFModel

## Pre-release checklist

- [ ] `version` in `pyproject.toml` matches `src/rdfmodel/__init__.py` and `CHANGELOG.md`
- [ ] `pytest` and `ruff check src tests` pass (CI on `main`)
- [ ] Update `CHANGELOG.md` date and release notes
- [ ] `python -m build` and `twine check dist/*` pass

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
