"""Data Integration Service for joining and consolidating data."""

from datetime import date
from typing import Any

from src.models.lot import Lot
from src.models.production_record import ProductionRecord
from src.models.quality_record import QualityRecord
from src.models.shipping_record import ShippingRecord


class DataIntegrationService:
    """Service for integrating data from three sources using composite keys."""

    def __init__(self) -> None:
        self._stats: dict[str, int] = {
            "production_records": 0,
            "quality_records": 0,
            "shipping_records": 0,
            "integrated_records": 0,
        }

    def integrate_all_sources(
        self,
        production_records: list[ProductionRecord],
        quality_records: list[QualityRecord],
        shipping_records: list[ShippingRecord],
    ) -> list[dict[str, Any]]:
        """
        Create integrated view using composite key (Lot ID + Date).

        (AC 2: Data must be joined using composite key of Lot ID and Date)

        Args:
            production_records: Production data from file
            quality_records: Quality inspection data from file
            shipping_records: Shipping data from file

        Returns:
            List of integrated records
        """
        self._stats["production_records"] = len(production_records)
        self._stats["quality_records"] = len(quality_records)
        self._stats["shipping_records"] = len(shipping_records)

        joined = self.join_production_quality(production_records, quality_records)
        joined = self.join_with_shipping(joined, shipping_records)

        results = list(joined.values())
        self._stats["integrated_records"] = len(results)
        return results

    def get_composite_key(
        self, lot_code: str, production_date: date
    ) -> tuple[str, date]:
        """Get composite key (lot_code, production_date)."""
        return (lot_code, production_date)

    def create_lot_from_production(self, production_record: dict[str, Any]) -> Lot:
        """Create a Lot entity from a production record."""
        production_date = production_record.get("production_date")
        if not isinstance(production_date, date):
            raise ValueError("production_date is required and must be a date")
        lot_code = str(production_record.get("lot_code", "")).strip()
        if not lot_code:
            raise ValueError("lot_code is required")
        return Lot(lot_code=lot_code, production_date=production_date)

    def join_production_quality(
        self,
        production_records: list[ProductionRecord],
        quality_records: list[QualityRecord],
    ) -> dict[tuple[str, date], dict[str, Any]]:
        """
        Join production and quality records on composite key.

        Returns:
            Dictionary mapping composite key to joined record
        """
        quality_by_lot: dict[int, QualityRecord] = {
            record.lot_id: record for record in quality_records
        }
        integrated: dict[tuple[str, date], dict[str, Any]] = {}

        for production in production_records:
            lot = Lot(
                lot_code=f"LOT-{production.lot_id:05d}",
                production_date=production.source_updated_timestamp.date(),
                id=production.lot_id,
                is_pending_inspection=True,
            )
            quality = quality_by_lot.get(production.lot_id)
            integrated[self.get_composite_key(lot.lot_code, lot.production_date)] = (
                self.build_integrated_record(lot, production, quality, None)
            )

        return integrated

    def join_with_shipping(
        self,
        integrated_records: dict[tuple[str, date], dict[str, Any]],
        shipping_records: list[ShippingRecord],
    ) -> dict[tuple[str, date], dict[str, Any]]:
        """
        Join the integrated records with shipping data on composite key.

        Returns:
            Dictionary mapping composite key to fully integrated record
        """
        shipping_by_lot: dict[int, ShippingRecord] = {
            record.lot_id: record for record in shipping_records
        }
        for record in integrated_records.values():
            lot: Lot = record["lot"]
            shipping = shipping_by_lot.get(lot.id or -1)
            record["shipping"] = shipping
        return integrated_records

    def build_integrated_record(
        self,
        lot: Lot,
        production_record: ProductionRecord | None,
        quality_record: QualityRecord | None,
        shipping_record: ShippingRecord | None,
    ) -> dict[str, Any]:
        """Build a single integrated record from components."""
        if quality_record is not None:
            lot.is_pending_inspection = False

        return {
            "lot": lot,
            "lot_code": lot.lot_code,
            "production_date": lot.production_date,
            "production": production_record,
            "quality": quality_record,
            "shipping": shipping_record,
        }

    def get_integration_statistics(self) -> dict[str, int]:
        """Get statistics about the last integration."""
        return dict(self._stats)
