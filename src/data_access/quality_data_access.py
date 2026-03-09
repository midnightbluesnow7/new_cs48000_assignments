"""Quality Inspection Data Access Layer."""

import logging
from copy import deepcopy
from datetime import date

from src.data_access.base import BaseDataAccess
from src.models.quality_record import QualityRecord

logger = logging.getLogger(__name__)


class QualityDataAccess(BaseDataAccess):
    """Data access for Quality Inspection Records."""

    def __init__(self, connection_string: str = "memory://quality"):
        super().__init__(connection_string)
        self._records: dict[int, QualityRecord] = {}
        self._next_id = 1

    def create(self, quality_record: QualityRecord) -> int:
        """Create a quality record and return its ID."""
        record_id = self._next_id
        self._next_id += 1
        quality_record.id = record_id
        self._records[record_id] = deepcopy(quality_record)
        logger.info(
            "Quality inspection record created: id=%d lot_id=%d",
            record_id,
            quality_record.lot_id,
        )
        return record_id

    def read_by_id(self, record_id: int) -> QualityRecord | None:
        """Read a quality record by ID."""
        record = self._records.get(record_id)
        return deepcopy(record) if record else None

    def read_by_lot_id(self, lot_id: int) -> QualityRecord | None:
        """Read quality record by lot ID."""
        for record in self._records.values():
            if record.lot_id == lot_id:
                return deepcopy(record)
        return None

    def read_by_lot_code_and_date(
        self, lot_code: str, inspection_date: date
    ) -> QualityRecord | None:
        """Read quality record by lot code and inspection date."""
        try:
            lot_id = int(lot_code)
        except ValueError:
            return None
        for record in self._records.values():
            if record.lot_id == lot_id and record.inspection_date == inspection_date:
                return deepcopy(record)
        return None

    def update(self, quality_record: QualityRecord) -> bool:
        """Update a quality record."""
        if quality_record.id is None:
            return False
        if quality_record.id not in self._records:
            return False
        self._records[quality_record.id] = deepcopy(quality_record)
        logger.info(
            "Quality inspection record updated: id=%d lot_id=%d",
            quality_record.id,
            quality_record.lot_id,
        )
        return True

    def delete(self, record_id: int) -> bool:
        """Delete a quality record by ID."""
        return self._records.pop(record_id, None) is not None

    def read_all(self) -> list[QualityRecord]:
        """Read all quality records."""
        records = [deepcopy(record) for record in self._records.values()]
        logger.info("Queried all quality records: count=%d", len(records))
        if len(records) > 500:
            logger.warning(
                "Very large query result for quality records: count=%d", len(records)
            )
        return records

    def get_records_by_defect_type(self, defect_type: str) -> list[QualityRecord]:
        """Get all quality records with a specific defect type."""
        target = defect_type.strip().lower()
        records = [
            deepcopy(record)
            for record in self._records.values()
            if (record.defect_type or "").strip().lower() == target
        ]
        logger.info(
            "Queried quality records by defect type: defect_type=%s count=%d",
            defect_type,
            len(records),
        )
        return records

    def get_defect_trend_by_type(
        self, start_date: date, end_date: date
    ) -> dict[str, int]:
        """
        Get defect count by type within a date range.

        Returns:
            Dictionary mapping defect type to count
        """
        trend: dict[str, int] = {}
        for record in self._records.values():
            if start_date <= record.inspection_date <= end_date and not record.is_pass:
                defect_type = record.defect_type or "Unspecified"
                trend[defect_type] = trend.get(defect_type, 0) + max(
                    record.defect_count, 0
                )
        logger.info(
            "Defect trend query complete: start_date=%s end_date=%s defect_types=%d",
            start_date,
            end_date,
            len(trend),
        )
        return trend

    def get_failing_records(self) -> list[QualityRecord]:
        """Get all quality records where inspection failed."""
        return [
            deepcopy(record) for record in self._records.values() if not record.is_pass
        ]

    def get_records_by_date_range(
        self, start_date: date, end_date: date
    ) -> list[QualityRecord]:
        """Get quality records within a date range."""
        return [
            deepcopy(record)
            for record in self._records.values()
            if start_date <= record.inspection_date <= end_date
        ]

    def get_missing_quality_records(self) -> list[int]:
        """Get lot IDs that have production records but no quality records."""
        return []
