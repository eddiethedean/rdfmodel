"""Per-test-module unique ``Rdf.type_uri`` values to avoid registry collisions."""

from __future__ import annotations

import inspect
from pathlib import Path


def module_type_uri(local: str) -> str:
    """Return ``http://example.org/tests/<module>/<local>`` for the calling module."""
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        raise RuntimeError("module_type_uri() must be called from module scope")
    caller_file = frame.f_back.f_globals.get("__file__")
    if not caller_file:
        raise RuntimeError("module_type_uri() caller has no __file__")
    stem = Path(caller_file).stem
    return f"http://example.org/tests/{stem}/{local}"
