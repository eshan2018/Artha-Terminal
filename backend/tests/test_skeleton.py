"""Smoke tests for the M1 layer-package skeleton.

Assert that every layer package imports cleanly (the tree is buildable) and that
the module set matches the architecture map — no missing or unexpected layers.
"""
from __future__ import annotations

import importlib

import pytest

from tools.ci import architecture_map as amap

LAYER_PACKAGES = sorted(amap.ALLOWED_IMPORTS)


@pytest.mark.parametrize("package", LAYER_PACKAGES)
def test_layer_package_imports(package: str) -> None:
    assert importlib.import_module(package) is not None


def test_expected_layer_packages_present() -> None:
    assert set(LAYER_PACKAGES) == {
        "backend.platform",
        "backend.providers",
        "backend.providers.ports",
        "backend.domain",
        "backend.domain.model",
        "backend.ingestion",
        "backend.features",
        "backend.analytics",
        "backend.api",
        "backend.orchestration",
    }
