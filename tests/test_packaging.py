"""Packaging and PEP 561 markers."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from importlib.resources import files
from pathlib import Path


def test_py_typed_marker_in_source() -> None:
    path = Path(__file__).resolve().parents[1] / "src" / "triplemodel" / "py.typed"
    assert path.is_file()


def test_py_typed_marker_in_installed_package() -> None:
    pkg = files("triplemodel")
    assert (pkg / "py.typed").is_file()


def test_wheel_contains_py_typed() -> None:
    root = Path(__file__).resolve().parents[1]
    wheels = list((root / "dist").glob("triplemodel-*.whl"))
    if not wheels:
        subprocess.run(
            [sys.executable, "-m", "build", str(root)],
            check=True,
            capture_output=True,
        )
        wheels = list((root / "dist").glob("triplemodel-*.whl"))
    assert wheels, "expected a built wheel after python -m build"
    wheel = max(wheels, key=lambda p: p.stat().st_mtime)
    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
    assert any(n.endswith("triplemodel/py.typed") for n in names)
