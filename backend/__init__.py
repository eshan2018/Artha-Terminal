"""Nivesh Terminal backend — the layered application (L1–L9).

Architecture: docs/architecture/03-system-architecture.md. Layer boundaries are
CI-enforced by tools/ci (dependency-direction, no-vendor-above-L1, module-schema
isolation). Do not add cross-layer imports; change the layer graph only via an ADR.
"""
