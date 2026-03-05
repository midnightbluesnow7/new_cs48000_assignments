"""Data Integrity Flags Data Access Layer."""

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from src.data_access.base import BaseDataAccess
from src.models.data_integrity_flag import DataIntegrityFlag


class DataIntegrityAccess(BaseDataAccess):
    """Data access for Data Integrity Flags."""

    def __init__(self, connection_string: str = "memory://integrity"):
        super().__init__(connection_string)
        self._flags: dict[int, DataIntegrityFlag] = {}
        self._next_id = 1

    def create(self, flag: DataIntegrityFlag) -> int:
        """Create a data integrity flag and return its ID."""
        flag_id = self._next_id
        self._next_id += 1
        flag.id = flag_id
        self._flags[flag_id] = deepcopy(flag)
        return flag_id

    def read_by_id(self, flag_id: int) -> DataIntegrityFlag | None:
        """Read a data integrity flag by ID."""
        flag = self._flags.get(flag_id)
        return deepcopy(flag) if flag else None

    def update(self, flag: DataIntegrityFlag) -> bool:
        """Update a data integrity flag."""
        if flag.id is None:
            return False
        if flag.id not in self._flags:
            return False
        self._flags[flag.id] = deepcopy(flag)
        return True

    def delete(self, flag_id: int) -> bool:
        """Delete a data integrity flag by ID."""
        return self._flags.pop(flag_id, None) is not None

    def read_all(self) -> list[DataIntegrityFlag]:
        """Read all data integrity flags."""
        return [deepcopy(flag) for flag in self._flags.values()]

    def get_flags_by_lot_id(self, lot_id: int) -> list[DataIntegrityFlag]:
        """Get all flags associated with a specific lot."""
        return [
            deepcopy(flag) for flag in self._flags.values() if flag.lot_id == lot_id
        ]

    def get_unresolved_flags(self) -> list[DataIntegrityFlag]:
        """Get all unresolved data integrity flags."""
        return [deepcopy(flag) for flag in self._flags.values() if not flag.is_resolved]

    def get_critical_flags(self) -> list[DataIntegrityFlag]:
        """Get all critical severity flags."""
        return [
            deepcopy(flag)
            for flag in self._flags.values()
            if flag.severity == "Critical"
        ]

    def get_flags_by_type(self, flag_type: str) -> list[DataIntegrityFlag]:
        """Get all flags of a specific type (e.g., 'Missing Quality')."""
        target = flag_type.strip().lower()
        return [
            deepcopy(flag)
            for flag in self._flags.values()
            if flag.flag_type.strip().lower() == target
        ]

    def resolve_flag(self, flag_id: int) -> bool:
        """Mark a flag as resolved."""
        flag = self._flags.get(flag_id)
        if flag is None:
            return False
        flag.resolve()
        return True

    def create_missing_quality_flag(self, lot_id: int) -> int:
        """Create a 'Missing Quality' flag for a lot (AC 4)."""
        return self.create(
            DataIntegrityFlag(
                lot_id=lot_id,
                flag_type="Missing Quality",
                severity="Error",
                description="Shipping record exists without corresponding quality record",
                detected_date=datetime.now(UTC),
            )
        )

    def create_date_conflict_flag(self, lot_id: int, description: str) -> int:
        """Create a 'Date Conflict' flag for a lot (AC 4)."""
        return self.create(
            DataIntegrityFlag(
                lot_id=lot_id,
                flag_type="Date Conflict",
                severity="Critical",
                description=description,
                detected_date=datetime.now(UTC),
            )
        )

    def get_integrity_summary(self) -> dict[str, Any]:
        """
        Get summary of data integrity issues.

        Returns:
            Dictionary with counts by severity and type
        """
        by_type: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        unresolved = 0
        for flag in self._flags.values():
            by_type[flag.flag_type] = by_type.get(flag.flag_type, 0) + 1
            by_severity[flag.severity] = by_severity.get(flag.severity, 0) + 1
            if not flag.is_resolved:
                unresolved += 1
        return {
            "total": len(self._flags),
            "unresolved": unresolved,
            "by_type": by_type,
            "by_severity": by_severity,
        }
