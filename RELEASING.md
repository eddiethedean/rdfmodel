# Releasing TripleModel

## 0.4.1 release readiness (repo)

| Item | Status |
|------|--------|
| Version `0.4.1` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| `CHANGELOG.md` — `## [0.4.1]` complete | Done |
| `examples/realworld/*` use `load_models`, `instance_of`, `ref_field`, `gYear` | Done |
| `tests/test_041_features.py`, `tests/test_realworld_examples.py` | Done |
| README / PLAN / ROADMAP reflect **0.4.1** beta | Done |

**Pre-release checklist (0.4.1)**

- [x] `version` `0.4.1` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] `pytest`, `ruff format --check`, `ruff check`, `ty check`
- [x] `PYTHONPATH=src python examples/realworld/*.py` (or CI `test_realworld_examples`)
- [ ] Create and push git tag `v0.4.1` (triggers Release workflow)
- [ ] GitHub release from tag; paste `## [0.4.1]` from `CHANGELOG.md`

```bash
git tag -a v0.4.1 -m "Release 0.4.1"
git push origin v0.4.1
```

---

## 0.4.0 release readiness (repo)

Verified on `main` before tagging `v0.4.0` (PyPI latest prior to this release: **0.3.0**).

| Item | Status |
|------|--------|
| Version `0.4.0` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| `docs/conf.py` release via `triplemodel.__version__` | Done |
| `CHANGELOG.md` — `## [0.4.0]` complete; `[Unreleased]` lists **0.4.1** planned work only | Done |
| `src/triplemodel/py.typed` in source and wheel (`tests/test_packaging.py`) | Done |
| Exit criteria `examples/exit_criteria_03.py`, `examples/exit_criteria_04.py` | Done |
| `examples/readme_examples.py`, `examples/realworld/*` (CI) | Done |
| sdist includes exit-criteria and `examples/realworld` (`pyproject.toml` `[tool.hatch.build.targets.sdist]`) | Done |
| README: beta status, file I/O, dispatch, inverse, limitations | Done |
| CI on push: `pytest` (100% cov), `build`, `ruff`, `ty` (Python 3.10–3.13) | Done |
| Docs workflow: `sphinx-build -W` | Done |
| Release workflow on tag: `pytest`, `build`, `twine check`, `ruff`, `ty`, `sphinx-build -W`, PyPI publish | Done |

**Remaining manual steps:** confirm `PYPI_API_TOKEN` in GitHub Actions secrets → tag `v0.4.0` → GitHub release → verify PyPI shows `0.4.0`.

## Pre-release checklist (0.4.0)

- [x] `version` `0.4.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] `[Unreleased]` contains only planned **0.4.1** work (no undocumented 0.4.0 changes)
- [x] CI on `main`: `pytest`, `ruff`, `ty`, `python -m build` (Python 3.10–3.13); Docs workflow
- [x] Local: `pytest`, `ruff format --check src tests`, `ruff check src tests`, `ty check src tests`
- [x] `PYTHONPATH=src python examples/exit_criteria_03.py`
- [x] `PYTHONPATH=src python examples/exit_criteria_04.py`
- [x] `PYTHONPATH=src python examples/readme_examples.py`
- [x] `python -m build` and `twine check dist/*` pass
- [ ] Create and push git tag `v0.4.0` (triggers Release workflow: build + PyPI publish)
- [ ] GitHub release from tag

## Publish to PyPI

### GitHub Actions (default)

1. In the repo **Settings → Secrets and variables → Actions**, add **`PYPI_API_TOKEN`**: a PyPI [API token](https://pypi.org/manage/account/token/) scoped to the `triplemodel` project (or the whole account for first release).
2. Push an annotated tag `v*` (e.g. `v0.4.0`). The [Release workflow](https://github.com/eddiethedean/triplemodel/blob/main/.github/workflows/release.yml) runs `pytest`, `ruff`, `ty`, `sphinx-build`, `python -m build`, `twine check`, uploads `dist/` as an artifact, then publishes with [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish).

### Manual fallback

```bash
python -m pip install build twine
python -m build
twine check dist/*
twine upload dist/*   # uses ~/.pypirc or PyPI token
```

## Read the Docs

After pushing to `main` (and after tagging for a versioned doc build if desired):

1. Import the project at [readthedocs.org](https://readthedocs.org/) (suggested slug: **triplemodel**).
2. Point it at `eddiethedean/triplemodel`; config file `.readthedocs.yaml` is used automatically.
3. Confirm the build is green; site URL: `https://triplemodel.readthedocs.io/`.
4. Optional: add the docs badge to `README.md` and set PyPI **Project-URL: Documentation** (already `https://triplemodel.readthedocs.io/` in `pyproject.toml`).

Local check: `pip install -e ".[docs]" && sphinx-build -b html docs docs/_build/html -W`.

## Git tag and GitHub release

```bash
git tag -a v0.4.0 -m "Release 0.4.0"
git push origin v0.4.0
```

Create a GitHub release from the tag and paste the `## [0.4.0]` section from `CHANGELOG.md` as release notes.
