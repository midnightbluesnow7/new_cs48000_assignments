"""Shipping Record domain model."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class ShippingRecord:
    """
    Shipping record from Shipping Logs (XLSX).

    Primary Key:
    - lot_id (foreign key to Lot) - unique 1:1 relationship
    - ship_date
    """

    lot_id: int
    ship_date: date
    destination_state: str
    carrier: str
    qty_shipped: int
    shipment_status: str
    source_updated_timestamp: datetime
    id: int | None = None

    def is_valid(self) -> bool:
        """Validate shipping record constraints."""
        if self.qty_shipped < 0:
            return False
        if not self.destination_state or not self.carrier:
            return False
        if not self.shipment_status:
            return False
        return True

    def get_status_description(self) -> str:
        """Get human-readable shipment status."""
        status = self.shipment_status.strip().lower()
        if status == "shipped":
            return "Shipment completed"
        if status in {"in transit", "in_transit"}:
            return "Shipment in transit"
        if status in {"hold", "on hold"}:
            return "Shipment on hold"
        return self.shipment_status

    def is_shipped(self) -> bool:
        """Check if lot has been shipped."""
        return self.shipment_status.strip().lower() == "shipped"
