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

The `compat` job installs **minimum** pins:

```text
pydantic==2.5.0
rdflib==7.0.0
```

and runs the full test suite (with `sqlalchemy` and `shacl` extras).

## Type checking

Public API typing is checked with **`ty`** (`ty check src tests`), not mypy. The package ships `py.typed` (PEP 561).
