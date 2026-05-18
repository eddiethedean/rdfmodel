# Releasing TripleModel

## 0.9.0 release readiness (repo)

| Item | Status |
|------|--------|
| Version `0.9.0` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| Matrix audit; plugin `register_parser` / `register_serializer` / `register_store` | Done |
| `docs/API_STABILITY.md`, `docs/cookbook/`, `docs/COMPATIBILITY.md` | Done |
| CI `compat` job (min pydantic / rdflib pins) | Done |
| Exit criteria `examples/exit_criteria_09.py` | Done |

**Pre-release checklist (0.9.0)**

- [x] `version` `0.9.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] Local gate: `make ci` and `make release-check`
- [x] `pytest` (100% cov), `ruff`, `ty`, `sphinx-build -W`
- [x] `examples/exit_criteria_09.py` in Makefile, release workflow, sdist
- [ ] Confirm `PYPI_API_TOKEN` in GitHub Actions secrets
- [ ] Create and push git tag `v0.9.0`

```bash
git tag -a v0.9.0 -m "Release 0.9.0"
git push origin v0.9.0
```

---

## 0.8.0 release readiness (repo)

| Item | Status |
|------|--------|
| Version `0.8.0` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| Stores, chunked/streaming import, strict mode, plugins, codegen CLI | Done |
| Exit criteria `examples/exit_criteria_08.py` (set `TRIPLEMODEL_BENCH_COUNT` for CI smoke) | Done |
| Guide `docs/guides/15-stores-scale-and-strict.md`; API `stores`, `plugins`, `codegen` | Done |
| Optional extras `sqlalchemy`, `berkeleydb`; CI `stores` job | Done |
| Release workflow includes `exit_criteria_08.py` | Done |

**Pre-release checklist (0.8.0)**

- [x] `version` `0.8.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] Local gate: `make ci` (matches CI + docs HTML) and `make release-check` (adds examples + `twine check`)
- [x] `pytest` (100% cov), `ruff format --check`, `ruff check`, `ty check`
- [x] `sphinx-build -b html docs docs/_build/html -W`
- [x] `examples/exit_criteria_08.py` and release workflow `exit_criteria_05`–`08` + `readme_examples.py`
- [ ] Confirm `PYPI_API_TOKEN` in GitHub Actions secrets
- [ ] Create and push git tag `v0.8.0`

```bash
git tag -a v0.8.0 -m "Release 0.8.0"
git push origin v0.8.0
```

---

## 0.7.0 release readiness (repo)

Verified on `main` after **v0.6.0**. PyPI latest before this release: **0.6.0**.

| Item | Status |
|------|--------|
| Version `0.7.0` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| `docs/conf.py` release via `triplemodel.__version__` | Done |
| `CHANGELOG.md` — `## [0.7.0]` complete (Added/Changed/Deferred); `[Unreleased]` stub | Done |
| Graph algorithms — `graphs_equal`, `graph_diff`, `model_diff`, CBD, RDFS dispatch, `hydrate_refs` | Done |
| Pre-release hardening — import skolemize once, `Rdf.resolve_subclass`, bulk dispatch discovery | Done |
| Exit criteria `examples/exit_criteria_07.py` (CBD + subclass dispatch) | Done |
| Guide `docs/guides/14-graph-algorithms-and-rdfs.md`; API `compare`, `cbd`, `rdfs`, `hydrate`, `vocab_registry` | Done |
| `examples/readme_examples.py`, `examples/realworld/*` (CI) | Done |
| README / PLAN / ROADMAP reflect **0.7.0** beta | Done |
| CI on push: `pytest` (100% cov), `build`, `ruff`, `ty` (Python 3.10–3.13) | Done |
| Release workflow on tag: `verify` job includes `exit_criteria_07.py` | Done |

**Before tagging:** commit and push all changes on `main` (audit fixes, docs, `tests/test_skolemize_import.py`). PyPI still shows **0.6.0** until `v0.7.0` is published.

**Pre-release checklist (0.7.0)**

- [x] `version` `0.7.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] `[Unreleased]` empty (all 0.7.0 notes under `## [0.7.0]`, including **Fixed** hardening)
- [x] `pytest` (542 tests, 100% cov), `ruff format --check`, `ruff check`, `ty check`
- [x] `sphinx-build -b html docs docs/_build/html -W`
- [x] `python -m build` and `twine check dist/*`
- [x] `PYTHONPATH=src python examples/exit_criteria_05.py`
- [x] `PYTHONPATH=src python examples/exit_criteria_06.py`
- [x] `PYTHONPATH=src python examples/exit_criteria_07.py`
- [x] `PYTHONPATH=src python examples/readme_examples.py`
- [ ] Confirm `PYPI_API_TOKEN` in GitHub Actions secrets
- [ ] Create and push git tag `v0.7.0` (triggers Release workflow)
- [ ] GitHub release from tag; paste `## [0.7.0]` from `CHANGELOG.md`
- [ ] Verify PyPI shows `triplemodel==0.7.0`

```bash
git tag -a v0.7.0 -m "Release 0.7.0"
git push origin v0.7.0
```

---

## 0.6.0 release readiness (repo)

Verified on `main` at commit `c6d022f` (prior tag: **v0.5.0**). PyPI latest before this release: **0.5.0**.

| Item | Status |
|------|--------|
| Version `0.6.0` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| `docs/conf.py` release via `triplemodel.__version__` | Done |
| `CHANGELOG.md` — `## [0.6.0]` complete (Added/Fixed/Changed); `[Unreleased]` stub | Done |
| SPARQL helpers — `ask`, `construct_models`, `select_models`, `load_sparql`, `apply_update`, `prepare_model_query`, `run_sparql`, etc. | Done |
| Exit criteria `examples/exit_criteria_06.py` (CONSTRUCT → models) | Done |
| Guide `docs/guides/13-sparql-and-endpoints.md`; API `docs/api/sparql.rst` | Done |
| `examples/readme_examples.py`, `examples/realworld/*` (CI) | Done |
| README / PLAN / ROADMAP reflect **0.6.0** beta | Done |
| CI on push: `pytest` (100% cov), `build`, `ruff`, `ty` (Python 3.10–3.13) | Done |
| Release workflow on tag: `verify` job includes `exit_criteria_06.py` | Done |

**Pre-release checklist (0.6.0)**

- [x] `version` `0.6.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] `[Unreleased]` empty (all 0.6.0 notes under `## [0.6.0]`)
- [x] `pytest`, `ruff format --check`, `ruff check`, `ty check`
- [x] `sphinx-build -b html docs docs/_build/html -W`
- [x] `python -m build` and `twine check dist/*`
- [x] `PYTHONPATH=src python examples/exit_criteria_05.py`
- [x] `PYTHONPATH=src python examples/exit_criteria_06.py`
- [x] `PYTHONPATH=src python examples/readme_examples.py`
- [ ] Confirm `PYPI_API_TOKEN` in GitHub Actions secrets
- [ ] Create and push git tag `v0.6.0` (triggers Release workflow)
- [ ] GitHub release from tag; paste `## [0.6.0]` from `CHANGELOG.md`
- [ ] Verify PyPI shows `triplemodel==0.6.0`

```bash
git tag -a v0.6.0 -m "Release 0.6.0"
git push origin v0.6.0
```

---

## 0.5.0 release readiness (repo)

Verified on `main` at commit `160a0bc` before tagging `v0.5.0` (prior tag: **v0.4.1**).

| Item | Status |
|------|--------|
| Version `0.5.0` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| `docs/conf.py` release via `triplemodel.__version__` | Done |
| `CHANGELOG.md` — `## [0.5.0]` complete (Added/Changed/Fixed); `[Unreleased]` stub | Done |
| `src/triplemodel/py.typed` in source and wheel (`tests/test_packaging.py`) | Done |
| Exit criteria `examples/exit_criteria_05.py` (named-graph TriG) | Done |
| Guide `docs/guides/12-datasets-and-named-graphs.md`; API exports `iter_model_quads`, `quads_in_context`, etc. | Done |
| `examples/readme_examples.py`, `examples/realworld/*` (CI) | Done |
| README / PLAN / ROADMAP reflect **0.5.0** beta | Done |
| CI on push: `pytest` (100% cov), `build`, `ruff`, `ty` (Python 3.10–3.13) | Done |
| Docs workflow: `sphinx-build -W` | Done (run locally before tag) |
| Release workflow on tag: `verify` job then `publish` (see `.github/workflows/release.yml`) | Configured |

**Pre-release checklist (0.5.0)**

- [x] `version` `0.5.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] `[Unreleased]` empty (all 0.5.0 notes under `## [0.5.0]`)
- [x] `pytest`, `ruff format --check`, `ruff check`, `ty check`
- [x] `sphinx-build -b html docs docs/_build/html -W`
- [x] `python -m build` and `twine check dist/*`
- [x] `PYTHONPATH=src python examples/exit_criteria_05.py`
- [x] `PYTHONPATH=src python examples/readme_examples.py`
- [ ] Confirm `PYPI_API_TOKEN` in GitHub Actions secrets
- [ ] Create and push git tag `v0.5.0` (triggers Release workflow)
- [ ] GitHub release from tag; paste `## [0.5.0]` from `CHANGELOG.md`
- [ ] Verify PyPI shows `triplemodel==0.5.0`

```bash
git tag -a v0.5.0 -m "Release 0.5.0"
git push origin v0.5.0
```

---

## 0.4.1 release readiness (repo)

Verified on `main` before tagging `v0.4.1` (prior tag: **v0.4.0**).

| Item | Status |
|------|--------|
| Version `0.4.1` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| `docs/conf.py` release via `triplemodel.__version__` | Done |
| `CHANGELOG.md` — `## [0.4.1]` complete (Added/Changed/Fixed); `[Unreleased]` empty | Done |
| `src/triplemodel/py.typed` in source and wheel (`tests/test_packaging.py`) | Done |
| Exit criteria `examples/exit_criteria_03.py`, `examples/exit_criteria_04.py` | Done |
| `examples/readme_examples.py`, `examples/realworld/*` (CI) | Done |
| README / PLAN / ROADMAP reflect **0.4.1** beta | Done |
| CI on push: `pytest` (100% cov), `build`, `ruff`, `ty` (Python 3.10–3.13) | Done |
| Docs workflow: `sphinx-build -W` | Done (run locally before tag) |
| Release workflow on tag: `pytest`, `build`, `twine check`, `ruff`, `ty`, `sphinx-build -W`, PyPI publish | Configured |

**Pre-release checklist (0.4.1)**

- [x] `version` `0.4.1` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] `[Unreleased]` empty (all 0.4.1 notes under `## [0.4.1]`)
- [x] `pytest`, `ruff format --check`, `ruff check`, `ty check`
- [x] `sphinx-build -b html docs docs/_build/html -W`
- [x] `python -m build` and `twine check dist/*`
- [x] `PYTHONPATH=src python examples/exit_criteria_03.py`
- [x] `PYTHONPATH=src python examples/exit_criteria_04.py`
- [x] `PYTHONPATH=src python examples/readme_examples.py`
- [ ] Confirm `PYPI_API_TOKEN` in GitHub Actions secrets
- [ ] Create and push git tag `v0.4.1` (triggers Release workflow)
- [ ] GitHub release from tag; paste `## [0.4.1]` from `CHANGELOG.md`
- [ ] Verify PyPI shows `triplemodel==0.4.1`

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
2. Push an annotated tag `v*` (e.g. `v0.5.0`). The [Release workflow](https://github.com/eddiethedean/triplemodel/blob/main/.github/workflows/release.yml) runs a **`verify`** job (`pytest`, `ruff`, `ty`, `sphinx-build -W`, exit-criteria examples, `python -m build`, `twine check`), uploads `dist/`, then a **`publish`** job (depends on `verify`) uploads to PyPI with [`pypa/gh-action-pypi-publish`](https://github.com/pypa/gh-action-pypi-publish).

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
