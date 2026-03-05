"""Quality Inspection Record domain model."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class QualityRecord:
    """
    Quality inspection record from Quality Inspection files (XLSX/CSV).

    Primary Key:
    - lot_id (foreign key to Lot)
    - inspection_date
    """

    lot_id: int
    inspection_date: date
    is_pass: bool
    inspector_id: str
    source_updated_timestamp: datetime
    defect_type: str | None = None
    defect_count: int = 0
    id: int | None = None

    def is_valid(self) -> bool:
        """Validate quality record constraints."""
        if not self.inspector_id:
            return False
        if self.defect_count < 0:
            return False
        if self.is_pass and self.defect_count > 0:
            return False
        return True

    def get_defect_description(self) -> str:
        """Get human-readable defect description."""
        if self.is_pass:
            return "No defects"
        defect = self.defect_type or "Unspecified"
        return f"{defect} ({self.defect_count})"

    def is_passing(self) -> bool:
        """Check if quality inspection passed."""
        return self.is_pass
