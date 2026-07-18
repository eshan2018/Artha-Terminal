"""Hermetic test configuration for the backend suites (doc 11).

Hypothesis is randomized by default, which would make CI failures unreproducible and
green runs unrepeatable — both disqualifying under doc 11's "no network, no services,
fixed seeds" rule. `derandomize` pins the generator so a given commit always explores
the same inputs; `deadline=None` removes the per-example timing check, which is a
wall-clock dependence dressed up as a correctness check.
"""
from hypothesis import HealthCheck, settings

settings.register_profile(
    "hermetic",
    derandomize=True,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
settings.load_profile("hermetic")
