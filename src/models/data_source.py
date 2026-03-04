"""Data Source Metadata domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class DataSource:
    """
    Operational metadata for monitoring data freshness and health.

    Primary Key:
    - source_name
    """

    source_name: str
    source_location: str
    file_format: str
    last_updated_timestamp: datetime
    refresh_status: Literal["Healthy", "Stale", "Error"] = "Healthy"
    id: int | None = None

    def mark_healthy(self) -> None:
        """Mark data source as healthy."""
        self.refresh_status = "Healthy"

    def mark_stale(self) -> None:
        """Mark data source as stale."""
        self.refresh_status = "Stale"

    def mark_error(self) -> None:
        """Mark data source as having an error."""
        self.refresh_status = "Error"

    def update_timestamp(self, timestamp: datetime) -> None:
        """Update the last updated timestamp."""
        self.last_updated_timestamp = timestamp

    def is_healthy(self) -> bool:
        """Check if data source is healthy."""
        return self.refresh_status == "Healthy"
