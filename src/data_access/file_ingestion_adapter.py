"""File Ingestion Adapter for reading from XLSX and CSV files."""

from datetime import datetime
from pathlib import Path
from typing import Any, cast

import pandas as pd


class FileIngestionError(RuntimeError):
    """Raised when ingestion fails due to missing or invalid files."""


class FileIngestionAdapter:
    """Adapter for reading data from XLSX and CSV files."""

    def __init__(self, source_location: str, file_format: str):
        """
        Initialize file ingestion adapter.

        Args:
            source_location: Path to file or directory
            file_format: File format ('XLSX', 'CSV')
        """
        self.source_location = source_location
        self.file_format = file_format.upper()

    def read_production_logs(self) -> list[dict[str, Any]]:
        """
        Read production logs from file.

        Returns:
            List of dictionaries representing production records
        """
        file_path = Path(self.source_location)
        if self.file_format == "CSV":
            return self._read_csv_file(str(file_path))
        if self.file_format == "XLSX":
            return self._read_xlsx_file(str(file_path))
        raise FileIngestionError(f"Unsupported format: {self.file_format}")

    def read_quality_logs(self) -> list[dict[str, Any]]:
        """
        Read quality inspection logs from file.

        Returns:
            List of dictionaries representing quality records
        """
        file_path = Path(self.source_location)
        if self.file_format == "CSV":
            return self._read_csv_file(str(file_path))
        if self.file_format == "XLSX":
            return self._read_xlsx_file(str(file_path))
        raise FileIngestionError(f"Unsupported format: {self.file_format}")

    def read_shipping_logs(self) -> list[dict[str, Any]]:
        """
        Read shipping logs from file.

        Returns:
            List of dictionaries representing shipping records
        """
        file_path = Path(self.source_location)
        if self.file_format == "CSV":
            return self._read_csv_file(str(file_path))
        if self.file_format == "XLSX":
            return self._read_xlsx_file(str(file_path))
        raise FileIngestionError(f"Unsupported format: {self.file_format}")

    def _read_xlsx_file(
        self, file_path: str, sheet_name: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Read data from XLSX file.

        Args:
            file_path: Path to XLSX file
            sheet_name: Name of sheet to read (optional)

        Returns:
            List of rows as dictionaries
        """
        path = Path(file_path)
        if not path.exists():
            raise FileIngestionError(f"File not found: {file_path}")
        frame = pd.read_excel(path, sheet_name=sheet_name)
        if isinstance(frame, dict):
            # pandas returns dict when sheet_name=None for all sheets; flatten rows.
            rows: list[dict[str, Any]] = []
            for data in frame.values():
                rows.extend(
                    data.where(pd.notna(data), None).to_dict("records")  # type: ignore[arg-type]
                )
            return rows
        return cast(
            list[dict[str, Any]],
            frame.where(pd.notna(frame), None).to_dict("records"),  # type: ignore[arg-type]
        )

    def _read_csv_file(self, file_path: str) -> list[dict[str, Any]]:
        """
        Read data from CSV file.

        Args:
            file_path: Path to CSV file

        Returns:
            List of rows as dictionaries
        """
        path = Path(file_path)
        if not path.exists():
            raise FileIngestionError(f"File not found: {file_path}")
        frame = pd.read_csv(path)
        return cast(
            list[dict[str, Any]],
            frame.where(pd.notna(frame), None).to_dict("records"),  # type: ignore[arg-type]
        )

    def validate_file_exists(self) -> bool:
        """Validate that the file or directory exists."""
        return Path(self.source_location).exists()

    def get_file_modification_time(self, file_path: str) -> str:
        """Get the file modification time."""
        path = Path(file_path)
        if not path.exists():
            raise FileIngestionError(f"File not found: {file_path}")
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat()
