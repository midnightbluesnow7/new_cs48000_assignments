"""Production Data Access Layer."""

from copy import deepcopy
from datetime import date

from src.data_access.base import BaseDataAccess
from src.models.production_record import ProductionRecord


class ProductionDataAccess(BaseDataAccess):
    """Data access for Production Records."""

    def __init__(self, connection_string: str = "memory://production"):
        super().__init__(connection_string)
        self._records: dict[int, ProductionRecord] = {}
        self._next_id = 1

    def create(self, production_record: ProductionRecord) -> int:
        """Create a production record and return its ID."""
        record_id = self._next_id
        self._next_id += 1
        production_record.id = record_id
        self._records[record_id] = deepcopy(production_record)
        return record_id

    def read_by_id(self, record_id: int) -> ProductionRecord | None:
        """Read a production record by ID."""
        record = self._records.get(record_id)
        return deepcopy(record) if record else None

    def read_by_lot_id(self, lot_id: int) -> ProductionRecord | None:
        """Read production record by lot ID."""
        for record in self._records.values():
            if record.lot_id == lot_id:
                return deepcopy(record)
        return None

    def read_by_lot_code_and_date(
        self, lot_code: str, production_date: date
    ) -> ProductionRecord | None:
        """Read production record by lot code and production date."""
        target = lot_code.strip().upper()
        for record in self._records.values():
            if (
                record.production_line_id.strip().upper() == target
                and record.source_updated_timestamp.date() == production_date
            ):
                return deepcopy(record)
        return None

    def update(self, production_record: ProductionRecord) -> bool:
        """Update a production record."""
        if production_record.id is None:
            return False
        if production_record.id not in self._records:
            return False
        self._records[production_record.id] = deepcopy(production_record)
        return True

    def delete(self, record_id: int) -> bool:
        """Delete a production record by ID."""
        return self._records.pop(record_id, None) is not None

    def read_all(self) -> list[ProductionRecord]:
        """Read all production records."""
        return [deepcopy(record) for record in self._records.values()]

    def get_records_by_production_line(
        self, production_line_id: str
    ) -> list[ProductionRecord]:
        """Get all production records for a specific production line."""
        target = production_line_id.strip().upper()
        return [
            deepcopy(record)
            for record in self._records.values()
            if record.production_line_id.strip().upper() == target
        ]

    def get_error_count_by_line_per_week(self, week_start_date: date) -> dict[str, int]:
        """
        Get error count by production line for a specific week.

        Returns:
            Dictionary mapping line ID to error count
        """
        result: dict[str, int] = {}
        week_end = week_start_date.toordinal() + 6
        for record in self._records.values():
            record_day = record.source_updated_timestamp.date().toordinal()
            if week_start_date.toordinal() <= record_day <= week_end:
                if record.has_line_issue or record.units_actual < record.units_planned:
                    line = record.production_line_id
                    result[line] = result.get(line, 0) + 1
        return result

    def get_records_by_date_range(
        self, start_date: date, end_date: date
    ) -> list[ProductionRecord]:
        """Get production records within a date range."""
        return [
            deepcopy(record)
            for record in self._records.values()
            if start_date <= record.source_updated_timestamp.date() <= end_date
        ]
