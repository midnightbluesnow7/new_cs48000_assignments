"""Playwright e2e tests for the Streamlit dashboard using test DB settings."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from pathlib import Path
from typing import Any
from urllib.request import urlopen

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(url: str, timeout_sec: float = 30.0) -> None:
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            with urlopen(url, timeout=2):
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Streamlit server did not become ready: {url}")


@pytest.fixture(scope="module")
def streamlit_base_url(database_url_test: str) -> Generator[str, None, None]:
    """Start Streamlit with test DB environment and return base URL."""
    streamlit = pytest.importorskip("streamlit")
    assert streamlit is not None

    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["DATABASE_URL"] = database_url_test
    env["FLASK_ENV"] = "testing"

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "main.py",
            "--server.headless",
            "true",
            "--server.port",
            str(port),
            "--server.address",
            "127.0.0.1",
        ],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        _wait_until_ready(base_url)
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=8)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.mark.e2e
def test_dashboard_loads_main_title(page: Any, streamlit_base_url: str) -> None:
    """Verify Streamlit app boots and renders the expected title."""
    page.goto(streamlit_base_url)
    page.wait_for_load_state("networkidle")
    expect_title = page.get_by_text("SteelWorks Operations Data Hub")
    expect_title.wait_for(timeout=15000)


@pytest.mark.e2e
def test_navigation_to_shipment_search_and_input(
    page: Any, streamlit_base_url: str
) -> None:
    """Verify Shipment Search view is reachable and accepts lot input."""
    page.goto(streamlit_base_url)
    page.wait_for_load_state("networkidle")

    page.get_by_text("Shipment Search", exact=True).click()
    lot_input = page.get_by_placeholder("LOT-20251219-003")
    lot_input.fill("LOT-20251219-003")

    assert lot_input.input_value() == "LOT-20251219-003"


@pytest.mark.e2e
def test_navigation_to_data_integrity_page(page: Any, streamlit_base_url: str) -> None:
    """Verify Data Integrity tab renders key metric area."""
    page.goto(streamlit_base_url)
    page.wait_for_load_state("networkidle")

    page.get_by_text("Data Integrity", exact=True).click()
    metric_text = page.get_by_text("Total Flags")
    metric_text.wait_for(timeout=15000)
