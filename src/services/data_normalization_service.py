"""Data Normalization Service for cleaning and standardizing data."""

from datetime import date
from typing import Any

from dateutil import parser


class DataNormalizationService:
    """Service for normalizing data from different sources."""

    def normalize_production_data(
        self, raw_records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Normalize production records (AC 2: Cleansing Logic).

        Cleansing operations:
        - Trim whitespace from string fields
        - Remove leading zeros from numeric fields
        - Standardize date format to YYYY-MM-DD

        Args:
            raw_records: Raw production records from file

        Returns:
            List of normalized production records
        """
        normalized = []
        for record in raw_records:
            normalized_record = self._trim_whitespace(record)
            normalized_record = self._remove_leading_zeros(normalized_record)
            if "production_date" in normalized_record:
                normalized_record["production_date"] = self._standardize_date(
                    normalized_record["production_date"]
                )
            if "date" in normalized_record:
                normalized_record["date"] = self._standardize_date(
                    normalized_record["date"]
                )
            if "lot_code" in normalized_record and isinstance(
                normalized_record["lot_code"], str
            ):
                normalized_record["lot_code"] = self._standardize_lot_id(
                    normalized_record["lot_code"]
                )
            normalized.append(normalized_record)
        return normalized

    def normalize_quality_data(
        self, raw_records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Normalize quality inspection records (AC 2: Cleansing Logic).

        Cleansing operations:
        - Trim whitespace from string fields
        - Remove leading zeros from numeric fields
        - Standardize date format to YYYY-MM-DD

        Args:
            raw_records: Raw quality records from file

        Returns:
            List of normalized quality records
        """
        normalized = []
        for record in raw_records:
            normalized_record = self._trim_whitespace(record)
            normalized_record = self._remove_leading_zeros(normalized_record)
            if "inspection_date" in normalized_record:
                normalized_record["inspection_date"] = self._standardize_date(
                    normalized_record["inspection_date"]
                )
            if "lot_code" in normalized_record and isinstance(
                normalized_record["lot_code"], str
            ):
                normalized_record["lot_code"] = self._standardize_lot_id(
                    normalized_record["lot_code"]
                )
            normalized.append(normalized_record)
        return normalized

    def normalize_shipping_data(
        self, raw_records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Normalize shipping records (AC 2: Cleansing Logic).

        Cleansing operations:
        - Trim whitespace from string fields
        - Remove leading zeros from numeric fields
        - Standardize date format to YYYY-MM-DD

        Args:
            raw_records: Raw shipping records from file

        Returns:
            List of normalized shipping records
        """
        normalized = []
        for record in raw_records:
            normalized_record = self._trim_whitespace(record)
            normalized_record = self._remove_leading_zeros(normalized_record)
            if "ship_date" in normalized_record:
                normalized_record["ship_date"] = self._standardize_date(
                    normalized_record["ship_date"]
                )
            if "lot_code" in normalized_record and isinstance(
                normalized_record["lot_code"], str
            ):
                normalized_record["lot_code"] = self._standardize_lot_id(
                    normalized_record["lot_code"]
                )
            normalized.append(normalized_record)
        return normalized

    def _trim_whitespace(self, record: dict[str, Any]) -> dict[str, Any]:
        """Trim whitespace from all string values in record."""
        trimmed = {}
        for key, value in record.items():
            if isinstance(value, str):
                trimmed[key] = value.strip()
            else:
                trimmed[key] = value
        return trimmed

    def _remove_leading_zeros(self, record: dict[str, Any]) -> dict[str, Any]:
        """Remove leading zeros from numeric string fields."""
        processed = {}
        for key, value in record.items():
            if isinstance(value, str):
                # Remove leading zeros from numeric strings
                # But preserve strings that start with non-digit characters
                if value and value[0].isdigit():
                    processed[key] = value.lstrip("0") or "0"
                else:
                    processed[key] = value
            else:
                processed[key] = value
        return processed

    def _standardize_date(self, date_value: Any) -> date:
        """Convert various date formats to standard YYYY-MM-DD format."""
        if isinstance(date_value, date):
            return date_value
        if date_value is None:
            raise ValueError("Date value cannot be None")
        parsed = parser.parse(str(date_value), dayfirst=False, yearfirst=False)
        return date(parsed.year, parsed.month, parsed.day)

    def _standardize_lot_id(self, lot_id: str) -> str:
        """Standardize lot ID (trim and remove leading zeros)."""
        cleaned = lot_id.strip()
        if cleaned.isdigit():
            return cleaned.lstrip("0") or "0"
        return cleaned

    def validate_normalized_record(
        self, record: dict[str, Any], record_type: str
    ) -> bool:
        """Validate that normalized record has required fields."""
        required_fields: dict[str, set[str]] = {
            "production": {"lot_code", "production_line_id"},
            "quality": {"lot_code", "inspection_date"},
            "shipping": {"lot_code", "ship_date"},
        }
        fields = required_fields.get(record_type.lower())
        if fields is None:
            return False
        for field in fields:
            if field not in record:
                return False
            if record[field] in (None, ""):
                return False
        return True
