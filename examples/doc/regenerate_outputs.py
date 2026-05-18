#!/usr/bin/env python3
"""Run all doc snippets and write ``outputs/<name>.txt`` (stdout)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNIPPETS = Path(__file__).resolve().parent / "snippets"
OUTPUTS = Path(__file__).resolve().parent / "outputs"


def run_snippet(path: Path) -> str:
    env = {
        **dict(__import__("os").environ),
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


def main() -> None:
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    for path in sorted(SNIPPETS.glob("*.py")):
        if path.name.startswith("_"):
            continue
        out = OUTPUTS / f"{path.stem}.txt"
        stdout = run_snippet(path)
        out.write_text(stdout, encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")
    print("All doc outputs regenerated.")


if __name__ == "__main__":
    main()
