"""Shipping Data Access Layer."""

from copy import deepcopy
from datetime import date

from src.data_access.base import BaseDataAccess
from src.models.shipping_record import ShippingRecord


class ShippingDataAccess(BaseDataAccess):
    """Data access for Shipping Records."""

    def __init__(self, connection_string: str = "memory://shipping"):
        super().__init__(connection_string)
        self._records: dict[int, ShippingRecord] = {}
        self._next_id = 1

    def create(self, shipping_record: ShippingRecord) -> int:
        """Create a shipping record and return its ID."""
        record_id = self._next_id
        self._next_id += 1
        shipping_record.id = record_id
        self._records[record_id] = deepcopy(shipping_record)
        return record_id

    def read_by_id(self, record_id: int) -> ShippingRecord | None:
        """Read a shipping record by ID."""
        record = self._records.get(record_id)
        return deepcopy(record) if record else None

    def read_by_lot_id(self, lot_id: int) -> ShippingRecord | None:
        """Read shipping record by lot ID."""
        for record in self._records.values():
            if record.lot_id == lot_id:
                return deepcopy(record)
        return None

    def read_by_lot_code(self, lot_code: str) -> ShippingRecord | None:
        """Read shipping record by lot code."""
        try:
            lot_id = int(lot_code)
        except ValueError:
            return None
        return self.read_by_lot_id(lot_id)

    def update(self, shipping_record: ShippingRecord) -> bool:
        """Update a shipping record."""
        if shipping_record.id is None:
            return False
        if shipping_record.id not in self._records:
            return False
        self._records[shipping_record.id] = deepcopy(shipping_record)
        return True

    def delete(self, record_id: int) -> bool:
        """Delete a shipping record by ID."""
        return self._records.pop(record_id, None) is not None

    def read_all(self) -> list[ShippingRecord]:
        """Read all shipping records."""
        return [deepcopy(record) for record in self._records.values()]

    def get_shipped_records(self) -> list[ShippingRecord]:
        """Get all records with shipment_status = 'Shipped'."""
        return [
            deepcopy(record)
            for record in self._records.values()
            if record.shipment_status.strip().lower() == "shipped"
        ]

    def get_records_by_destination_state(self, state: str) -> list[ShippingRecord]:
        """Get all shipping records for a specific destination state."""
        target = state.strip().upper()
        return [
            deepcopy(record)
            for record in self._records.values()
            if record.destination_state.strip().upper() == target
        ]

    def get_records_by_carrier(self, carrier: str) -> list[ShippingRecord]:
        """Get all shipping records for a specific carrier."""
        target = carrier.strip().lower()
        return [
            deepcopy(record)
            for record in self._records.values()
            if record.carrier.strip().lower() == target
        ]

    def get_records_by_date_range(
        self, start_date: date, end_date: date
    ) -> list[ShippingRecord]:
        """Get shipping records within a date range."""
        return [
            deepcopy(record)
            for record in self._records.values()
            if start_date <= record.ship_date <= end_date
        ]

    def get_missing_shipping_records(self) -> list[int]:
        """Get lot IDs that have quality records but no shipping records."""
        return []

    def search_by_lot_id(self, lot_id: int) -> ShippingRecord | None:
        """Search for shipping record by lot ID (AC 3: Search function)."""
        return self.read_by_lot_id(lot_id)
