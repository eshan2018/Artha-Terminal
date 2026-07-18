"""Architecture guardrails for the Nivesh Terminal backend.

Custom, dependency-free (stdlib-only) AST lints that enforce the frozen
architecture (docs/architecture/) in CI:

- dependency-direction  (doc 03 / ADR-0002)
- no-vendor-above-L1    (doc 06 / ADR-0005)
- module-schema-isolation (ADR-0003)

Rationale for custom checks vs a third-party import linter: see
docs/implementation/01-engineering-decisions.md (ED-008).
"""
