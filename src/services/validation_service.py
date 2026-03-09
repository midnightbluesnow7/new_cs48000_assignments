"""Validation Service for detecting data integrity issues and outliers."""

import logging
from datetime import UTC, date, datetime
from typing import Any

from src.models.data_integrity_flag import DataIntegrityFlag
from src.models.lot import Lot

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating data integrity and detecting outliers."""

    def __init__(self) -> None:
        self._summary = {
            "date_conflicts": 0,
            "production_invalid": 0,
            "quality_invalid": 0,
            "shipping_invalid": 0,
            "total_flags": 0,
        }

    def detect_date_conflicts(
        self, integrated_records: dict[tuple[str, date], dict[str, Any]]
    ) -> list[DataIntegrityFlag]:
        """
        Detect logical date errors (AC 4: Outlier Detection).

        Flag records where Ship Date is earlier than Production Date.

        Args:
            integrated_records: Dictionary of integrated records

        Returns:
            List of DataIntegrityFlag for date conflicts
        """
        flags: list[DataIntegrityFlag] = []
        for record in integrated_records.values():
            lot: Lot = record["lot"]
            shipping = record.get("shipping")
            if shipping is None:
                continue
            is_valid, flag = self.validate_ship_date_after_production_date(
                lot=lot,
                production_date=lot.production_date,
                ship_date=shipping.ship_date,
            )
            if not is_valid and flag is not None:
                logger.warning(
                    "Date conflict detected: lot_code=%s production_date=%s ship_date=%s",
                    lot.lot_code,
                    lot.production_date,
                    shipping.ship_date,
                )
                flags.append(flag)
                lot.flag_date_conflict()
        self._summary["date_conflicts"] = len(flags)
        self._summary["total_flags"] += len(flags)
        if flags:
            logger.warning(
                "Date conflict validation complete: conflicts_detected=%d", len(flags)
            )
        return flags

    def validate_ship_date_after_production_date(
        self, lot: Lot, production_date: date, ship_date: date
    ) -> tuple[bool, DataIntegrityFlag | None]:
        """
        Validate that ship date is not before production date.

        Returns:
            Tuple of (is_valid, flag_if_invalid)
        """
        if ship_date < production_date:
            return False, self.create_date_conflict_flag(
                lot, production_date, ship_date
            )
        return True, None

    def detect_all_outliers(
        self, integrated_records: dict[tuple[str, date], dict[str, Any]]
    ) -> list[DataIntegrityFlag]:
        """
        Detect all data quality outliers and inconsistencies.

        Checks:
        - Date conflicts (ship < production)
        - Missing required fields
        - Invalid field values

        Returns:
            List of all detected DataIntegrityFlag objects
        """
        flags: list[DataIntegrityFlag] = []
        flags.extend(self.detect_date_conflicts(integrated_records))
        for record in integrated_records.values():
            production = record.get("production")
            quality = record.get("quality")
            shipping = record.get("shipping")
            if production is not None:
                valid, _ = self.validate_production_record(production.__dict__)
                if not valid:
                    self._summary["production_invalid"] += 1
            if quality is not None:
                valid, _ = self.validate_quality_record(quality.__dict__)
                if not valid:
                    self._summary["quality_invalid"] += 1
            if shipping is not None:
                valid, _ = self.validate_shipping_record(shipping.__dict__)
                if not valid:
                    self._summary["shipping_invalid"] += 1
        return flags

    def validate_production_record(
        self, record: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """
        Validate a production record for data quality.

        Returns:
            Tuple of (is_valid, error_message_if_invalid)
        """
        required = ["lot_id", "production_line_id", "units_planned", "units_actual"]
        for field in required:
            if field not in record:
                return False, f"Missing field: {field}"
        if int(record["units_planned"]) < 0 or int(record["units_actual"]) < 0:
            return False, "Units cannot be negative"
        return True, None

    def validate_quality_record(
        self, record: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """
        Validate a quality record for data quality.

        Returns:
            Tuple of (is_valid, error_message_if_invalid)
        """
        required = ["lot_id", "inspection_date", "is_pass"]
        for field in required:
            if field not in record:
                return False, f"Missing field: {field}"
        defect_count = int(record.get("defect_count", 0))
        if defect_count < 0:
            return False, "Defect count cannot be negative"
        return True, None

    def validate_shipping_record(
        self, record: dict[str, Any]
    ) -> tuple[bool, str | None]:
        """
        Validate a shipping record for data quality.

        Returns:
            Tuple of (is_valid, error_message_if_invalid)
        """
        required = ["lot_id", "ship_date", "qty_shipped", "shipment_status"]
        for field in required:
            if field not in record:
                return False, f"Missing field: {field}"
        if int(record["qty_shipped"]) < 0:
            return False, "Quantity shipped cannot be negative"
        return True, None

    def create_date_conflict_flag(
        self, lot: Lot, production_date: date, ship_date: date
    ) -> DataIntegrityFlag:
        """Create a date conflict integrity flag."""
        return DataIntegrityFlag(
            lot_id=lot.id or 0,
            flag_type="Date Conflict",
            severity="Critical",
            description=(
                f"Lot {lot.lot_code} ship date {ship_date.isoformat()} is earlier than "
                f"production date {production_date.isoformat()}"
            ),
            detected_date=datetime.now(UTC),
        )

    def get_validation_summary(self) -> dict[str, int]:
        """Get summary of validation results."""
        return dict(self._summary)
