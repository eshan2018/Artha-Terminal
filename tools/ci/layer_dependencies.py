"""Guardrail: dependency-direction (doc 03 / ADR-0002).

A module may import only the kernel, its own subpackages, and the layers explicitly
permitted by ``architecture_map.ALLOWED_IMPORTS``. Any "upward" or otherwise illegal
import is a violation.
"""
from __future__ import annotations

from pathlib import Path

from . import architecture_map as amap
from ._scan import Violation, is_backend_module, iter_imports, iter_source_files

RULE = "dependency-direction"


def check(backend_dir: Path) -> list[Violation]:
    violations: list[Violation] = []
    for src in iter_source_files(backend_dir):
        importer_layer = amap.layer_of(src.module)
        if importer_layer is None:
            continue
        for imp in iter_imports(src):
            if not is_backend_module(imp.module):
                continue  # stdlib / third-party imports are not governed by layer rules
            target_layer = amap.layer_of(imp.module)
            if target_layer is None:
                continue
            if amap.import_permitted(importer_layer, target_layer):
                continue
            allowed = sorted(amap.ALLOWED_IMPORTS.get(importer_layer, frozenset()))
            violations.append(
                Violation(
                    RULE,
                    src.path,
                    imp.lineno,
                    f"{importer_layer} may not import {target_layer} (via '{imp.module}'). "
                    f"Allowed targets: {amap.KERNEL}, own subpackages, {allowed}.",
                )
            )
    return violations
