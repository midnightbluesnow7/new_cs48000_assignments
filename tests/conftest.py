"""Shared pytest fixtures for integration and e2e suites."""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
ENV_TEST_PATH = ROOT / ".env.test"


@pytest.fixture(scope="session", autouse=True)
def load_test_environment() -> None:
    """Load `.env.test` values for all tests."""
    if ENV_TEST_PATH.exists():
        load_dotenv(ENV_TEST_PATH, override=True)


@pytest.fixture(scope="session")
def database_url_test() -> str:
    """Return test database URL from environment."""
    url = os.getenv("DATABASE_URL_TEST")
    if not url:
        pytest.skip("DATABASE_URL_TEST is not configured in .env.test")
    return url
