"""Guardrail: no-vendor-name-above-L1 (doc 06 / ADR-0005).

A vendor token (e.g. ``yfinance``) may appear only inside that vendor's adapter
package. Anywhere else in the backend it is a violation — vendor knowledge is
quarantined at L1 so every provider stays replaceable.

The check inspects imports and *code* identifiers (not docstrings/comments), so
prose that merely mentions a vendor does not trip it, but ``import yfinance`` or
``yfinance.download(...)`` does.
"""
from __future__ import annotations

from pathlib import Path

from . import architecture_map as amap
from ._scan import (
    SourceFile,
    Violation,
    iter_code_identifiers,
    iter_imports,
    iter_source_files,
)

RULE = "no-vendor-above-L1"


def check(backend_dir: Path) -> list[Violation]:
    violations: list[Violation] = []
    for src in iter_source_files(backend_dir):
        for token in amap.VENDOR_ALLOWED_PREFIX:
            if amap.vendor_home(src.module, token):
                continue  # this is the vendor's own adapter home — allowed
            for lineno in _token_hits(src, token):
                violations.append(
                    Violation(
                        RULE,
                        src.path,
                        lineno,
                        f"vendor name '{token}' may not appear above L1 "
                        f"(only under {amap.VENDOR_ALLOWED_PREFIX[token]}).",
                    )
                )
    return violations


def _token_hits(src: SourceFile, token: str) -> list[int]:
    lines: set[int] = set()
    for imp in iter_imports(src):
        if imp.root == token or imp.module == token or imp.module.startswith(token + "."):
            lines.add(imp.lineno)
    for name, lineno in iter_code_identifiers(src.tree):
        if name == token:
            lines.add(lineno)
    return sorted(lines)
