"""Conflict Resolution Service for handling missing data and inconsistencies."""

import logging
from datetime import UTC, date, datetime
from typing import Any

from src.models.data_integrity_flag import DataIntegrityFlag
from src.models.lot import Lot

logger = logging.getLogger(__name__)


class ConflictResolutionService:
    """Service for resolving conflicts and handling missing data."""

    def resolve_missing_quality_records(
        self, integrated_records: dict[tuple[str, date], dict[str, Any]]
    ) -> list[DataIntegrityFlag]:
        """
        Handle missing quality records (AC 2: Conflict Resolution).

        If a Lot ID exists in Production but is missing in Quality,
        the record must still appear but be flagged as "Pending Inspection."

        Args:
            integrated_records: Dictionary of integrated records

        Returns:
            List of DataIntegrityFlag for missing quality records
        """
        flags: list[DataIntegrityFlag] = []
        for record in integrated_records.values():
            lot: Lot = record["lot"]
            if record.get("quality") is None:
                logger.warning(
                    "Missing inspection data: lot_code=%s has no quality record",
                    lot.lot_code,
                )
                self.flag_lot_pending_inspection(lot)
                flags.append(self.create_pending_inspection_flag(lot))
        if flags:
            logger.warning(
                "Missing quality inspection records detected: count=%d", len(flags)
            )
        return flags

    def resolve_missing_shipping_records(
        self, integrated_records: dict[tuple[str, date], dict[str, Any]]
    ) -> list[DataIntegrityFlag]:
        """
        Identify lots that appear in Shipping but have no Quality record.

        (AC 4: Data Integrity Flags highlight any Lot IDs in Shipping
        with no corresponding Quality record)

        Args:
            integrated_records: Dictionary of integrated records

        Returns:
            List of DataIntegrityFlag for inconsistencies
        """
        flags: list[DataIntegrityFlag] = []
        for record in integrated_records.values():
            lot: Lot = record["lot"]
            has_shipping = record.get("shipping") is not None
            has_quality = record.get("quality") is not None
            if has_shipping and not has_quality:
                logger.warning(
                    "Missing inspection data: lot_code=%s has shipping record but no quality record",
                    lot.lot_code,
                )
                lot.flag_data_integrity_issue()
                flags.append(self.create_missing_quality_flag(lot))
        if flags:
            logger.warning(
                "Lots with shipping but missing quality records detected: count=%d",
                len(flags),
            )
        return flags

    def flag_lot_pending_inspection(self, lot: Lot) -> None:
        """Mark a lot as pending inspection."""
        lot.mark_pending_inspection()

    def create_pending_inspection_flag(self, lot: Lot) -> DataIntegrityFlag:
        """Create a 'Pending Inspection' flag for a lot."""
        return DataIntegrityFlag(
            lot_id=lot.id or 0,
            flag_type="Pending Inspection",
            severity="Warning",
            description=f"Lot {lot.lot_code} has no quality inspection record",
            detected_date=datetime.now(UTC),
        )

    def create_missing_quality_flag(self, lot: Lot) -> DataIntegrityFlag:
        """Create a 'Missing Quality' integrity flag."""
        return DataIntegrityFlag(
            lot_id=lot.id or 0,
            flag_type="Missing Quality",
            severity="Error",
            description=f"Lot {lot.lot_code} has shipping data but no quality record",
            detected_date=datetime.now(UTC),
        )

    def create_missing_shipping_flag(self, lot: Lot) -> DataIntegrityFlag:
        """Create a 'Missing Shipping' integrity flag."""
        return DataIntegrityFlag(
            lot_id=lot.id or 0,
            flag_type="Missing Shipping",
            severity="Warning",
            description=f"Lot {lot.lot_code} has no shipping record",
            detected_date=datetime.now(UTC),
        )

    def handle_orphaned_records(
        self,
        production_only: list[Lot],
        quality_only: list[Lot],
        shipping_only: list[Lot],
    ) -> list[DataIntegrityFlag]:
        """
        Handle records that exist in only one source.

        Returns:
            List of created DataIntegrityFlag objects
        """
        flags: list[DataIntegrityFlag] = []
        for lot in production_only:
            self.flag_lot_pending_inspection(lot)
            flags.append(self.create_pending_inspection_flag(lot))
        for lot in quality_only:
            lot.flag_data_integrity_issue()
            flags.append(self.create_missing_shipping_flag(lot))
        for lot in shipping_only:
            lot.flag_data_integrity_issue()
            flags.append(self.create_missing_quality_flag(lot))
        return flags
