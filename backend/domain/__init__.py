"""L5 · Domain store — canonical model + module-owned repositories/schemas.
Owning docs: 04, 07. Data-owning modules under here own their schema and must not
read each other’s internals (ADR-0003). May import: backend.domain.model, platform.
"""
