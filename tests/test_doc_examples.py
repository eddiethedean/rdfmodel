"""Runnable documentation snippets and golden stdout outputs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNIPPETS = ROOT / "examples" / "doc" / "snippets"
OUTPUTS = ROOT / "examples" / "doc" / "outputs"


def _snippet_paths() -> list[Path]:
    return sorted(p for p in SNIPPETS.glob("*.py") if not p.name.startswith("_"))


def _run_snippet(path: Path) -> str:
    env = {
        **__import__("os").environ,
        "PYTHONPATH": f"{ROOT / 'src'}{__import__('os').pathsep}{ROOT}",
    }
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


@pytest.mark.parametrize("snippet", _snippet_paths(), ids=lambda p: p.stem)
def test_doc_snippet_matches_golden_output(snippet: Path) -> None:
    expected_path = OUTPUTS / f"{snippet.stem}.txt"
    assert expected_path.is_file(), f"missing golden output: {expected_path}"
    assert _run_snippet(snippet) == expected_path.read_text(encoding="utf-8")


def test_regenerate_outputs_script_runs() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "examples" / "doc" / "regenerate_outputs.py")],
        cwd=ROOT,
        check=True,
    )
