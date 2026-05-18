"""Paths to bundled RDF data for real-world examples."""

from __future__ import annotations

from pathlib import Path

REALWORLD_DIR = Path(__file__).resolve().parent
DATA_DIR = REALWORLD_DIR / "data"


def data_file(name: str) -> Path:
    path = DATA_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Missing bundled data file: {path}")
    return path
