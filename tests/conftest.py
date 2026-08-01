"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest

from src.cache import cache


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the in-memory cache before each test."""
    cache.clear()
    yield
    cache.clear()