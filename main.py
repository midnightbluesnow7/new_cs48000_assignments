"""Main entry point for SteelWorks Operations Data Hub."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import streamlit as st

from config import Config
from src.data_access.data_source_metadata_access import DataSourceMetadataAccess
from src.data_access.file_ingestion_adapter import (
    FileIngestionAdapter,
    FileIngestionError,
)
from src.models.data_source import DataSource
from src.models.production_record import ProductionRecord
from src.models.quality_record import QualityRecord
from src.models.shipping_record import ShippingRecord
from src.presentation.dashboard import Dashboard
from src.services.conflict_resolution_service import ConflictResolutionService
from src.services.data_integration_service import DataIntegrationService
from src.services.data_normalization_service import DataNormalizationService
from src.services.validation_service import ValidationService


def _safe_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "yes", "y", "1", "pass"}


def main() -> None:
    """
    Main entry point for the application.

    Orchestrates:
    1. Automated Multi-Source Ingestion (AC 1)
    2. Data Normalization & Relational Mapping (AC 2)
    3. Integrated Problem Reporting (AC 3)
    4. Automated Validation & Exception Handling (AC 4)
    """
    initialize_database()
    trigger_data_ingestion_and_integration()
    start_dashboard()


def initialize_database() -> None:
    """Initialize database connection and tables."""
    metadata_access = DataSourceMetadataAccess()
    now = datetime.now(UTC)
    if not metadata_access.read_all():
        metadata_access.create(
            DataSource(
                source_name=Config.PRODUCTION_LOGS_SOURCE_NAME,
                source_location="data/Ops_Production_Log.xlsx",
                file_format="XLSX",
                last_updated_timestamp=now,
            )
        )
        metadata_access.create(
            DataSource(
                source_name=Config.QUALITY_LOGS_SOURCE_NAME,
                source_location="data/Ops_Quality_Log.xlsx",
                file_format="XLSX",
                last_updated_timestamp=now,
                refresh_status="Stale",
            )
        )
        metadata_access.create(
            DataSource(
                source_name=Config.SHIPPING_LOGS_SOURCE_NAME,
                source_location="data/Ops_Shipping_Log.xlsx",
                file_format="XLSX",
                last_updated_timestamp=now,
            )
        )
    st.session_state["source_metadata_access"] = metadata_access


def trigger_data_ingestion_and_integration() -> None:
    """
    Trigger the complete data ingestion and integration pipeline.

    1. Load data from files (FileIngestionAdapter)
    2. Normalize data (DataNormalizationService)
    3. Integrate from all sources (DataIntegrationService)
    4. Resolve conflicts (ConflictResolutionService)
    5. Validate data (ValidationService)
    6. Persist to database
    """
    normalizer = DataNormalizationService()
    integration_service = DataIntegrationService()
    conflict_service = ConflictResolutionService()
    validation_service = ValidationService()

    production_rows: list[dict[str, Any]] = []
    shipping_rows: list[dict[str, Any]] = []
    quality_rows: list[dict[str, Any]] = []

    production_path = Path("data/Ops_Production_Log.xlsx")
    shipping_path = Path("data/Ops_Shipping_Log.xlsx")
    quality_path = Path("data/Ops_Quality_Log.xlsx")

    try:
        production_rows = FileIngestionAdapter(
            source_location=str(production_path), file_format="XLSX"
        ).read_production_logs()
    except FileIngestionError:
        production_rows = []

    try:
        shipping_rows = FileIngestionAdapter(
            source_location=str(shipping_path), file_format="XLSX"
        ).read_shipping_logs()
    except FileIngestionError:
        shipping_rows = []

    if quality_path.exists():
        try:
            quality_rows = FileIngestionAdapter(
                source_location=str(quality_path), file_format="XLSX"
            ).read_quality_logs()
        except FileIngestionError:
            quality_rows = []

    normalized_production = normalizer.normalize_production_data(
        [
            {
                "lot_code": str(row.get("Lot ID", "")).strip().upper(),
                "production_line_id": str(
                    row.get("Production Line", "Unknown")
                ).strip(),
                "shift": str(row.get("Shift", "")).strip(),
                "units_planned": _safe_int(row.get("Units Planned")),
                "units_actual": _safe_int(row.get("Units Actual")),
                "downtime_minutes": _safe_int(row.get("Downtime (min)")),
                "has_line_issue": _safe_bool(row.get("Line Issue?")),
                "production_date": row.get("Date"),
            }
            for row in production_rows
        ]
    )

    normalized_shipping = normalizer.normalize_shipping_data(
        [
            {
                "lot_code": str(row.get("Lot ID", "")).strip().upper(),
                "ship_date": row.get("Ship Date"),
                "destination_state": str(row.get("Destination (State)", "")).strip(),
                "carrier": str(row.get("Carrier", "")).strip(),
                "qty_shipped": _safe_int(row.get("Qty Shipped")),
                "shipment_status": str(row.get("Ship Status", "")).strip(),
            }
            for row in shipping_rows
        ]
    )

    normalized_quality = normalizer.normalize_quality_data(
        [
            {
                "lot_code": str(row.get("Lot ID", "")).strip().upper(),
                "inspection_date": row.get("Inspection Date"),
                "is_pass": _safe_bool(row.get("Inspection Result")),
                "defect_type": row.get("Defect Type"),
                "defect_count": _safe_int(row.get("Defect Count")),
                "inspector_id": str(row.get("Inspector ID", "AUTO")).strip() or "AUTO",
            }
            for row in quality_rows
        ]
    )

    lot_id_lookup: dict[str, int] = {}
    next_lot_id = 1

    def lot_id_for(lot_code: str) -> int:
        nonlocal next_lot_id
        if lot_code not in lot_id_lookup:
            lot_id_lookup[lot_code] = next_lot_id
            next_lot_id += 1
        return lot_id_lookup[lot_code]

    production_records = [
        ProductionRecord(
            lot_id=lot_id_for(record["lot_code"]),
            production_line_id=str(record["production_line_id"]),
            shift=str(record["shift"]),
            units_planned=_safe_int(record["units_planned"]),
            units_actual=_safe_int(record["units_actual"]),
            downtime_minutes=_safe_int(record.get("downtime_minutes")),
            has_line_issue=_safe_bool(record.get("has_line_issue")),
            source_updated_timestamp=datetime.combine(
                record["production_date"], datetime.min.time()
            ),
        )
        for record in normalized_production
        if normalizer.validate_normalized_record(record, "production")
    ]

    quality_records = [
        QualityRecord(
            lot_id=lot_id_for(record["lot_code"]),
            inspection_date=record["inspection_date"],
            is_pass=_safe_bool(record["is_pass"]),
            defect_type=(
                str(record.get("defect_type")).strip()
                if record.get("defect_type")
                else None
            ),
            defect_count=_safe_int(record.get("defect_count")),
            inspector_id=str(record.get("inspector_id", "AUTO")),
            source_updated_timestamp=datetime.now(UTC),
        )
        for record in normalized_quality
        if normalizer.validate_normalized_record(record, "quality")
    ]

    shipping_records = [
        ShippingRecord(
            lot_id=lot_id_for(record["lot_code"]),
            ship_date=record["ship_date"],
            destination_state=str(record["destination_state"]),
            carrier=str(record["carrier"]),
            qty_shipped=_safe_int(record["qty_shipped"]),
            shipment_status=str(record["shipment_status"]),
            source_updated_timestamp=datetime.now(UTC),
        )
        for record in normalized_shipping
        if normalizer.validate_normalized_record(record, "shipping")
    ]

    integrated_records = integration_service.integrate_all_sources(
        production_records, quality_records, shipping_records
    )

    integrated_by_key = {
        (record["lot_code"], record["production_date"]): record
        for record in integrated_records
    }
    pending_flags = conflict_service.resolve_missing_quality_records(integrated_by_key)
    missing_quality_flags = conflict_service.resolve_missing_shipping_records(
        integrated_by_key
    )
    date_conflict_flags = validation_service.detect_date_conflicts(integrated_by_key)

    st.session_state["integrated_records"] = list(integrated_by_key.values())
    st.session_state["integrity_flags"] = [
        {
            "lot_code": next(
                (
                    record["lot"].lot_code
                    for record in integrated_by_key.values()
                    if (record["lot"].id or 0) == flag.lot_id
                ),
                "UNKNOWN",
            ),
            "flag_type": flag.flag_type,
            "severity": flag.severity,
            "description": flag.description,
        }
        for flag in [*pending_flags, *missing_quality_flags, *date_conflict_flags]
    ]

    source_health = {
        Config.PRODUCTION_LOGS_SOURCE_NAME: {
            "status": "Healthy" if production_rows else "Error",
            "last_updated": datetime.now(UTC).isoformat(),
        },
        Config.QUALITY_LOGS_SOURCE_NAME: {
            "status": "Healthy" if quality_rows else "Stale",
            "last_updated": datetime.now(UTC).isoformat(),
        },
        Config.SHIPPING_LOGS_SOURCE_NAME: {
            "status": "Healthy" if shipping_rows else "Error",
            "last_updated": datetime.now(UTC).isoformat(),
        },
    }
    st.session_state["source_health"] = source_health


def start_dashboard() -> None:
    """Start the Streamlit dashboard."""
    Dashboard().run()


if __name__ == "__main__":
    main()
