"""Production Record domain model."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProductionRecord:
    """
    Production record from Production Logs (CSV).

    Primary Key:
    - lot_id (foreign key to Lot)
    - production_date (derived from Lot)
    """

    lot_id: int
    production_line_id: str
    shift: str
    units_planned: int
    units_actual: int
    downtime_minutes: int
    has_line_issue: bool
    source_updated_timestamp: datetime
    id: int | None = None

    def get_line_error_rate(self) -> float:
        """Calculate error rate for production line."""
        if self.units_planned <= 0:
            return 0.0
        shortfall = max(self.units_planned - self.units_actual, 0)
        return shortfall / self.units_planned

    def is_valid(self) -> bool:
        """Validate production record constraints."""
        if not self.production_line_id or not self.shift:
            return False
        if self.units_planned < 0 or self.units_actual < 0:
            return False
        if self.downtime_minutes < 0:
            return False
        return True

    def mark_line_issue(self) -> None:
        """Mark that this production line has an issue."""
        self.has_line_issue = True
