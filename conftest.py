"""Ensure the repository root is importable so `backend` and `tools` resolve as
top-level packages during tests, regardless of install mode.
"""
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parent)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
