"""Shared, stdlib-only AST scanning helpers for the architecture lints.

Import resolution is done statically from source text — the guardrails never
import or execute the code they check, so they run in any environment.
"""
from __future__ import annotations

import ast
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from . import architecture_map as amap


@dataclass(frozen=True)
class SourceFile:
    module: str  # dotted, e.g. "backend.analytics.engine"
    is_package: bool  # True for __init__.py
    path: Path
    tree: ast.Module


@dataclass(frozen=True)
class ImportRef:
    module: str  # resolved dotted target ("" if an unresolvable relative import)
    root: str  # top-level token, e.g. "backend" or "yfinance"
    lineno: int


@dataclass(frozen=True)
class Violation:
    rule: str
    path: Path
    lineno: int
    message: str

    def format(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        return f"{rel}:{self.lineno}: [{self.rule}] {self.message}"


def iter_source_files(backend_dir: Path) -> Iterator[SourceFile]:
    """Yield every ``.py`` file under ``backend_dir`` as a parsed :class:`SourceFile`.

    Module names are reconstructed relative to ``backend_dir.parent`` so they carry
    the ``backend.`` prefix the architecture map expects.
    """
    for path in sorted(backend_dir.rglob("*.py")):
        rel = path.relative_to(backend_dir.parent)
        parts = list(rel.with_suffix("").parts)
        is_package = parts[-1] == "__init__"
        if is_package:
            parts = parts[:-1]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        yield SourceFile(module=".".join(parts), is_package=is_package, path=path, tree=tree)


def iter_imports(src: SourceFile) -> Iterator[ImportRef]:
    """Yield each import in ``src``, resolving relative imports against its module."""
    for node in ast.walk(src.tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield ImportRef(alias.name, alias.name.split(".")[0], node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                resolved = _resolve_relative(src, node.level, node.module)
                root = resolved.split(".")[0] if resolved else ""
                yield ImportRef(resolved, root, node.lineno)
            else:
                mod = node.module or ""
                yield ImportRef(mod, mod.split(".")[0], node.lineno)


def _resolve_relative(src: SourceFile, level: int, submodule: str | None) -> str:
    base = src.module.split(".")
    if not src.is_package:
        base = base[:-1]  # a module's anchor is its containing package
    up = level - 1
    if up:
        base = base[:-up] if up <= len(base) else []
    if submodule:
        base = base + submodule.split(".")
    return ".".join(p for p in base if p)


def iter_code_identifiers(tree: ast.Module) -> Iterator[tuple[str, int]]:
    """Yield ``(name, lineno)`` for *code* identifiers only — :class:`ast.Name` and
    the attribute of :class:`ast.Attribute` — never string/docstring constants or
    comments. This is what makes vendor-isolation a check on code, not on prose that
    merely mentions a vendor.
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            yield node.id, node.lineno
        elif isinstance(node, ast.Attribute):
            yield node.attr, node.lineno


def is_backend_module(module: str) -> bool:
    return module == amap.PACKAGE_ROOT or module.startswith(amap.PACKAGE_ROOT + ".")
