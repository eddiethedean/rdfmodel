# Compatibility matrix

TripleModel is tested against the dependency ranges declared in `pyproject.toml` and against pinned minimum versions in CI.

## Supported versions

| Component | Minimum | Maximum (tested) |
|-----------|---------|------------------|
| Python | 3.10 | 3.13 |
| pydantic | 2.5 | latest 2.x (`<3`) |
| rdflib | 7.0 | latest 7.x (`<8`) |

## Optional extras

| Extra | Purpose |
|-------|---------|
| `shacl` | `pyshacl` validation |
| `sqlalchemy` | SQLAlchemy RDF store |
| `berkeleydb` | BerkeleyDB store (not on Windows) |
| `dev` | pytest, ruff, ty, coverage |

## CI

The main `test` job runs on Python 3.10–3.13 with current dependency releases.

The `compat` job runs the full test suite with 100% coverage (same as the main `test` job):

| Python | Pins |
|--------|------|
| 3.10 | `pydantic==2.5.0` and `rdflib==7.0.0` |
| 3.13 | `rdflib==7.0.0` only (pydantic from `pyproject.toml`; 2.5 has no 3.13 wheels) |

Minimum **pydantic 2.5** is validated on 3.10–3.12 via the 3.10 compat leg and local `make compat` (use `make compat-rdflib` on 3.13).

## Type checking

Public API typing is checked with **`ty`** (`ty check src tests`), not mypy. The package ships `py.typed` (PEP 561).
