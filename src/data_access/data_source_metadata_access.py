"""Data Source Metadata Data Access Layer."""

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, Literal, cast

from src.data_access.base import BaseDataAccess
from src.models.data_source import DataSource


class DataSourceMetadataAccess(BaseDataAccess):
    """Data access for Data Source Metadata."""

    def __init__(self, connection_string: str = "memory://sources"):
        super().__init__(connection_string)
        self._sources: dict[int, DataSource] = {}
        self._next_id = 1

    def create(self, data_source: DataSource) -> int:
        """Create a data source metadata record and return its ID."""
        source_id = self._next_id
        self._next_id += 1
        data_source.id = source_id
        self._sources[source_id] = deepcopy(data_source)
        return source_id

    def read_by_id(self, metadata_id: int) -> DataSource | None:
        """Read a data source metadata by ID."""
        source = self._sources.get(metadata_id)
        return deepcopy(source) if source else None

    def read_by_source_name(self, source_name: str) -> DataSource | None:
        """Read data source metadata by source name."""
        target = source_name.strip().lower()
        for source in self._sources.values():
            if source.source_name.strip().lower() == target:
                return deepcopy(source)
        return None

    def update(self, data_source: DataSource) -> bool:
        """Update a data source metadata record."""
        if data_source.id is None:
            return False
        if data_source.id not in self._sources:
            return False
        self._sources[data_source.id] = deepcopy(data_source)
        return True

    def delete(self, metadata_id: int) -> bool:
        """Delete a data source metadata record by ID."""
        return self._sources.pop(metadata_id, None) is not None

    def read_all(self) -> list[DataSource]:
        """Read all data source metadata records."""
        return [deepcopy(source) for source in self._sources.values()]

    def update_last_updated_timestamp(
        self, source_name: str, timestamp: datetime
    ) -> bool:
        """Update the last updated timestamp for a data source."""
        target = source_name.strip().lower()
        for source in self._sources.values():
            if source.source_name.strip().lower() == target:
                source.last_updated_timestamp = timestamp
                return True
        return False

    def update_refresh_status(self, source_name: str, status: str) -> bool:
        """Update the refresh status for a data source."""
        if status not in {"Healthy", "Stale", "Error"}:
            return False
        target = source_name.strip().lower()
        for source in self._sources.values():
            if source.source_name.strip().lower() == target:
                source.refresh_status = cast(
                    Literal["Healthy", "Stale", "Error"], status
                )
                return True
        return False

    def get_source_health_dashboard(self) -> dict[str, Any]:
        """
        Get status dashboard showing all data sources and their health.

        Returns:
            Dictionary mapping source name to health info (status, last_updated)
        """
        return {
            source.source_name: {
                "status": source.refresh_status,
                "last_updated": source.last_updated_timestamp.isoformat(),
                "location": source.source_location,
                "file_format": source.file_format,
            }
            for source in self._sources.values()
        }

    def get_stale_sources(self, stale_threshold_hours: int = 24) -> list[DataSource]:
        """Get data sources that haven't been updated within threshold."""
        now = datetime.now(UTC)
        stale_sources: list[DataSource] = []
        for source in self._sources.values():
            elapsed_hours = (now - source.last_updated_timestamp).total_seconds() / 3600
            if elapsed_hours > stale_threshold_hours:
                stale_sources.append(deepcopy(source))
        return stale_sources

    def mark_all_sources_as_updating(self) -> None:
        """Mark all sources as currently updating."""
        for source in self._sources.values():
            source.refresh_status = "Stale"
