"""Integration tests against the configured PostgreSQL test database."""

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_SQL = ROOT / "db" / "schema.sql"


def _seed_minimal_test_data(cursor: Any) -> None:
    """Insert deterministic records used by integration assertions."""
    cursor.execute(
        """
        INSERT INTO data_source_metadatas (
            source_name, source_location, file_format, last_updated_timestamp, refresh_status
        ) VALUES
            ('Production Logs', '/tmp/prod.xlsx', 'xlsx', CURRENT_TIMESTAMP, 'Healthy'),
            ('Quality Logs', '/tmp/quality.xlsx', 'xlsx', CURRENT_TIMESTAMP, 'Healthy'),
            ('Shipping Logs', '/tmp/ship.xlsx', 'xlsx', CURRENT_TIMESTAMP, 'Healthy');

        INSERT INTO lots (
            id, lot_code, production_date, is_pending_inspection, has_data_integrity_issue, has_date_conflict
        ) VALUES
            (1, 'LOT-TEST-001', DATE '2026-01-10', TRUE, FALSE, FALSE),
            (2, 'LOT-TEST-002', DATE '2026-01-11', FALSE, FALSE, FALSE),
            (3, 'LOT-TEST-003', DATE '2026-01-12', FALSE, FALSE, FALSE);

        INSERT INTO production_records (
            lot_id, production_line_id, shift, units_planned, units_actual, downtime_minutes,
            has_line_issue, source_updated_timestamp
        ) VALUES
            (1, 'Line 1', 'Day', 100, 90, 10, TRUE, CURRENT_TIMESTAMP),
            (2, 'Line 2', 'Night', 120, 120, 0, FALSE, CURRENT_TIMESTAMP),
            (3, 'Line 1', 'Swing', 130, 125, 5, FALSE, CURRENT_TIMESTAMP);

        INSERT INTO quality_inspection_records (
            lot_id, inspection_date, is_pass, defect_type, defect_count, inspector_id, source_updated_timestamp
        ) VALUES
            (2, DATE '2026-01-12', FALSE, 'Functional', 3, 'I-001', CURRENT_TIMESTAMP),
            (3, DATE '2026-01-13', TRUE, NULL, 0, 'I-002', CURRENT_TIMESTAMP);

        INSERT INTO shipping_records (
            lot_id, ship_date, destination_state, carrier, qty_shipped, shipment_status, source_updated_timestamp
        ) VALUES
            (2, DATE '2026-01-10', 'IN', 'XPO', 40, 'Shipped', CURRENT_TIMESTAMP),
            (3, DATE '2026-01-15', 'OH', 'UPS Freight', 80, 'Shipped', CURRENT_TIMESTAMP);
        """
    )


@pytest.fixture(scope="session")
def db_connection(database_url_test: str) -> Generator[Any, None, None]:
    """Provide a PostgreSQL connection initialized with schema and seed data."""
    psycopg2 = pytest.importorskip("psycopg2")

    try:
        conn = psycopg2.connect(database_url_test)
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Cannot connect to test database: {exc}")

    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")

    cursor.execute(SCHEMA_SQL.read_text(encoding="utf-8"))
    _seed_minimal_test_data(cursor)

    yield conn

    cursor.close()
    conn.close()


@pytest.mark.integration
def test_schema_tables_exist(db_connection: Any) -> None:
    """Verify core tables are created in the test database."""
    cursor = db_connection.cursor()
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
    )
    table_names = {row[0] for row in cursor.fetchall()}
    cursor.close()

    expected = {
        "data_integrity_flags",
        "data_source_metadatas",
        "lots",
        "production_records",
        "quality_inspection_records",
        "shipping_records",
    }
    assert expected.issubset(table_names)


@pytest.mark.integration
def test_seed_data_loaded_into_core_tables(db_connection: Any) -> None:
    """Verify seed script inserts data into critical tables."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM lots;")
    lot_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM production_records;")
    production_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM shipping_records;")
    shipping_count = cursor.fetchone()[0]
    cursor.close()

    assert lot_count > 0
    assert production_count > 0
    assert shipping_count > 0


@pytest.mark.integration
def test_lot_status_query_returns_operational_status(db_connection: Any) -> None:
    """Validate the AC3 lot status search query returns a recognized status."""
    cursor = db_connection.cursor()
    cursor.execute(
        """
        SELECT
            l.lot_code,
            CASE
                WHEN sr.shipment_status IS NOT NULL THEN 'Shipped'
                WHEN qr.is_pass = FALSE THEN 'Failed Quality'
                WHEN l.is_pending_inspection = TRUE THEN 'Pending Inspection'
                ELSE 'In Production'
            END AS current_operational_status
        FROM lots l
        LEFT JOIN quality_inspection_records qr ON l.id = qr.lot_id
        LEFT JOIN shipping_records sr ON l.id = sr.lot_id
        ORDER BY l.id
        LIMIT 1;
        """
    )
    row = cursor.fetchone()
    cursor.close()

    assert row is not None
    lot_code, status = row
    assert isinstance(lot_code, str)
    assert status in {
        "Shipped",
        "Failed Quality",
        "Pending Inspection",
        "In Production",
    }


@pytest.mark.integration
def test_data_integrity_conflict_query_executes(db_connection: Any) -> None:
    """Ensure date conflict audit query runs on test data without errors."""
    cursor = db_connection.cursor()
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM lots l
        JOIN shipping_records sr ON l.id = sr.lot_id
        WHERE sr.ship_date < l.production_date;
        """
    )
    count = cursor.fetchone()[0]
    cursor.close()

    assert isinstance(count, int)
    assert count >= 0
