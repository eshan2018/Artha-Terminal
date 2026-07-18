"""Guardrail: module-schema isolation (ADR-0003).

Each data-owning domain module owns its schema and must not read another module's
internals. Cross-module data access goes through a published repository interface,
never a direct import of the peer module. The shared canonical vocabulary
(``backend.domain.model``) is exempt — it is vocabulary, not a data module.
"""
from __future__ import annotations

from pathlib import Path

from . import architecture_map as amap
from ._scan import Violation, iter_imports, iter_source_files

RULE = "module-schema-isolation"


def check(backend_dir: Path) -> list[Violation]:
    violations: list[Violation] = []
    for src in iter_source_files(backend_dir):
        owner = amap.domain_module_of(src.module)
        if owner is None:
            continue  # not inside a data-owning domain module
        for imp in iter_imports(src):
            if not imp.module.startswith(amap.DOMAIN_ROOT):
                continue
            target = amap.domain_module_of(imp.module)
            if target is None or target == owner:
                continue  # shared model or same module — fine
            violations.append(
                Violation(
                    RULE,
                    src.path,
                    imp.lineno,
                    f"{owner} must not read another module's schema/internals "
                    f"({target} via '{imp.module}'); cross-module access goes through a "
                    f"published repository interface (ADR-0003).",
                )
            )
    return violations
