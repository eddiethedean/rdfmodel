# Documentation examples

Runnable snippets for the README and Sphinx guides.

| Path | Purpose |
|------|---------|
| `snippets/*.py` | Self-contained scripts (run with repo root on `PYTHONPATH`) |
| `outputs/*.txt` | Captured stdout (golden files) |
| `regenerate_outputs.py` | Rebuild all `outputs/*.txt` after editing snippets |

```bash
PYTHONPATH=src:. python examples/doc/regenerate_outputs.py
pytest tests/test_doc_examples.py
```

CI runs every snippet via `tests/test_doc_examples.py` and checks stdout against `outputs/`.
