# Releasing TripleModel

## 0.12.0 (repo)

| Item | Status |
|------|--------|
| Version `0.12.0` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| `CHANGELOG.md` — `## [0.12.0]` (SparqlModel 0.13 mapping APIs); `[Unreleased]` empty | Done |
| `examples/doc/outputs/installation_version.txt` → `0.12.0` | Done |

**Pre-release checklist (0.12.0)**

- [x] `version` `0.12.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] Regenerate `examples/doc/outputs/` (`installation_version.txt` → `0.12.0`)
- [ ] `make lint` and `make test` on `main`
- [ ] Commit 0.12.0 version bump on `main`
- [ ] **Tag and publish** — create `v0.12.0` when approved for PyPI

```bash
git tag -a v0.12.0 -m "Release 0.12.0"
git push origin v0.12.0
```

## 0.11.0 (repo)

| Item | Status |
|------|--------|
| Version `0.11.0` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| `CHANGELOG.md` — `## [0.11.0]` (breaking + pyoxigraph surface); `[Unreleased]` empty | Done |
| `docs/MIGRATION_0.11.md`; `docs/API_STABILITY.md` 0.11 exception | Done |
| rdflib/SHACL removed; no `import rdflib` in `src/` | Done |
| pyoxigraph surface: `store/ops`, `query_results`, `canonicalize_quads`, parse flags, SPARQL dataset kwargs, `LangString.direction` | Done |
| `examples/stores/bulk_load_backup.py`; `make examples` includes it | Done |
| `examples/doc/outputs/installation_version.txt` → `0.11.0` | Done |
| `make ci` (pytest 100% cov, stores, compat, ruff, ty, sphinx `-W`) | Done (maintainer re-run before tag) |
| `make release-check` (ci + examples + `twine check`) | Done (maintainer re-run before tag) |

**Pre-release checklist (0.11.0)**

- [x] `version` `0.11.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] `[Unreleased]` empty in `CHANGELOG.md`
- [x] Regenerate `examples/doc/outputs/` (`installation_version.txt` → `0.11.0`)
- [x] Local gate: `make ci`
- [x] Local gate: `make release-check`
- [ ] Commit all 0.11.0 changes on `main` (rdflib removal + pyoxigraph surface)
- [ ] Confirm `PYPI_API_TOKEN` in GitHub Actions secrets (maintainer)
- [ ] **Tag and publish** — create `v0.11.0` only when approved for PyPI (see below)

**Publish (when tagging is approved)**

```bash
make release-check

git tag -a v0.11.0 -m "Release 0.11.0"
git push origin v0.11.0
```

Watch the **Release** workflow on GitHub Actions; confirm [PyPI](https://pypi.org/project/triplemodel/) shows `0.11.0`.

---

## 0.10.1 patch (repo)

| Item | Status |
|------|--------|
| Version `0.10.1` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| `CHANGELOG.md` — `## [0.10.1]` entry (includes I/O fixes on `main` after `decb741`) | Done |
| `infer_format` — removed formats + URL `?` / `#` suffix inference | Done |
| Parse I/O — `bytes` / `BytesIO` / `StringIO` via `data=`; dataset URL parity | Done |
| `merge_graphs` prefixes; `fetch_url` HTTP errors; JSON-LD / kwargs warnings | Done |
| `examples/realworld/schema_org_ngos.py` uses `triplemodel.vocab.XSD` | Done |
| GitHub **CI** + **Docs** green on `main` (`decb741`) | Done |
| Local `make release-check` (ci + examples + `twine check`) | Done (2026-05-20) |

**Pre-release checklist (0.10.1)**

- [x] `version` `0.10.1` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] `[Unreleased]` empty in `CHANGELOG.md`
- [x] Regenerate `examples/doc/outputs/` (including `installation_version.txt` → `0.10.1`)
- [x] Local gate: `make ci` (2026-05-20)
- [x] Local gate: `make release-check` (2026-05-20)
- [ ] Confirm `PYPI_API_TOKEN` in GitHub Actions secrets (maintainer)
- [ ] **Tag and publish** — create `v0.10.1` only when approved for PyPI (see below)

**Not yet on PyPI:** confirm latest tag on GitHub; ship when `v0.10.1` / `v0.11.0` is pushed and the Release workflow runs.

When publishing is approved:

```bash
make release-check
git tag -a v0.10.1 -m "Release 0.10.1"
git push origin v0.10.1
```

---

## 0.10.0 release readiness (repo)

| Item | Status |
|------|--------|
| Version `0.10.0` in `pyproject.toml` and `src/triplemodel/__init__.py` | Done |
| pyoxigraph engine; `triplemodel.Store`; migration guide `docs/MIGRATION_0.10.md` | Done |
| `CHANGELOG.md` — `## [0.10.0]` entry | Done |
| CI `compat` job (min pydantic / pyoxigraph pins) | Done |
| Release workflow calls reusable CI + Docs workflows before publish | Done |
| Exit criteria `examples/exit_criteria_09.py` (0.10 Store + disk smoke) | Done |
| `examples/stores/disk_store.py` | Done |
| 0.10 hygiene (parse leak, cleanup warnings, CI stores/shacl, Actions v5/v6) | Done |

**Pre-release checklist (0.10.0)**

- [x] `version` `0.10.0` in `pyproject.toml`, `src/triplemodel/__init__.py`, and `CHANGELOG.md`
- [x] Local gate: `make ci` and `make release-check` (verified 2026-05-19)
- [x] `pytest` (100% cov), `ruff format --check`, `ruff check`, `ty check`
- [x] `sphinx-build -b html docs docs/_build/html -W` (via `make ci` / `make docs`)
- [x] `make examples` (exit_criteria_03–09, `disk_store`, readme_examples)
- [ ] Confirm `PYPI_API_TOKEN` in GitHub Actions secrets (maintainer)
- [ ] **Tag and publish** — create `v0.10.0` only when approved for PyPI (see below)

**Publish (when tagging is approved)**

```bash
make release-check

git tag -a v0.10.0 -m "Release 0.10.0"
git push origin v0.10.0
```

Watch the **Release** workflow on GitHub Actions; confirm [PyPI](https://pypi.org/project/triplemodel/) shows `0.10.0`.

---

## Historical releases

Older checklists (0.9.0, 0.8.0, …) are preserved in git history. See `CHANGELOG.md` for shipped versions.
