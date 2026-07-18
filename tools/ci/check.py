"""Run every architecture guardrail over ``backend/`` and exit non-zero on any violation.

Usage:
    python -m tools.ci.check [BACKEND_DIR]

With no argument it locates ``backend/`` relative to the repository root. Intended
to be the single CI entry point for the layer guardrails.
"""
from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from . import layer_dependencies, module_schema_isolation, vendor_isolation
from ._scan import Violation

Check = Callable[[Path], list[Violation]]

CHECKS: tuple[Check, ...] = (
    layer_dependencies.check,
    vendor_isolation.check,
    module_schema_isolation.check,
)


def run(backend_dir: Path) -> list[Violation]:
    """Run all guardrails; return the combined list of violations."""
    violations: list[Violation] = []
    for check in CHECKS:
        violations.extend(check(backend_dir))
    return violations


def _default_backend_dir() -> Path:
    # tools/ci/check.py -> tools/ci -> tools -> <repo root>
    return Path(__file__).resolve().parents[2] / "backend"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:]) if argv is None else list(argv)
    backend_dir = Path(args[0]).resolve() if args else _default_backend_dir()
    if not backend_dir.is_dir():
        print(f"architecture-lint: backend dir not found: {backend_dir}", file=sys.stderr)
        return 2

    violations = run(backend_dir)
    root = backend_dir.parent
    if violations:
        print(f"architecture-lint: {len(violations)} violation(s):", file=sys.stderr)
        for v in sorted(violations, key=lambda x: (str(x.path), x.lineno, x.rule)):
            print("  " + v.format(root), file=sys.stderr)
        return 1
    print(f"architecture-lint: OK — no violations in {backend_dir.name}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
