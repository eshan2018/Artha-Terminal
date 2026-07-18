"""L7 · Analytics engines producing AnalyticResults. Consumes features and other
engines’ results only — never repositories. Owning doc: 08.
May import: backend.features, backend.domain.model, backend.platform.
"""
from backend.analytics import one_year_return

__all__ = ["one_year_return"]
