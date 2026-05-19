# Compatibility matrix

TripleModel is tested against the dependency ranges declared in `pyproject.toml` and against pinned minimum versions in CI.

## Supported versions

| Component | Minimum | Maximum (tested) |
|-----------|---------|------------------|
| Python | 3.10 | 3.13 |
| pydantic | 2.5 | latest 2.x (`<3`) |
| pyoxigraph | 0.5 | latest 0.5.x (`<0.6`) |

## Optional extras

| Extra | Purpose |
|-------|---------|
| `shacl` | `pyshacl` + `rdflib` (bridge for validation only) |
| `dev` | pytest, ruff, ty, coverage |

## CI

The main `test` job runs on Python 3.10–3.13 with current dependency releases.

The `compat` job runs the full test suite with 100% coverage:

| Python | Pins |
|--------|------|
| 3.10 | `pydantic==2.5.0` and `pyoxigraph==0.5.0` |
| 3.13 | `pyoxigraph==0.5.0` only (pydantic from `pyproject.toml`) |

## Type checking

Public API typing is checked with **`ty`** (`ty check src tests`), not mypy. The package ships `py.typed` (PEP 561).
