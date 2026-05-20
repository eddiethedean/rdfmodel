# Releasing TripleModel

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
