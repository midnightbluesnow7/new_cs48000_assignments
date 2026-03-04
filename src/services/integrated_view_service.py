"""Integrated View Service for generating operational reports."""

from collections import defaultdict
from datetime import date
from typing import Any

from src.models.lot import Lot


class IntegratedViewService:
    """Service for generating integrated operational views and reports."""

    def __init__(
        self,
        integrated_records: list[dict[str, Any]] | None = None,
        data_integrity_flags: list[dict[str, Any]] | None = None,
        source_health: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.integrated_records = integrated_records or []
        self.data_integrity_flags = data_integrity_flags or []
        self.source_health = source_health or {}

    def get_production_health_by_line_per_week(
        self, week_start_date: date
    ) -> list[dict[str, Any]]:
        """
        Get production health metrics for each line per week (AC 3.1).

        Identifies which production lines have the highest error rates per week.

        Args:
            week_start_date: Start date of the week

        Returns:
            List of line health records with error rates
        """
        week_end = week_start_date.toordinal() + 6
        counts: dict[str, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "issues": 0}
        )

        for record in self.integrated_records:
            production = record.get("production")
            lot: Lot | None = record.get("lot")
            if production is None or lot is None:
                continue
            day = lot.production_date.toordinal()
            if week_start_date.toordinal() <= day <= week_end:
                line = production.production_line_id
                counts[line]["total"] += 1
                if (
                    production.has_line_issue
                    or production.units_actual < production.units_planned
                ):
                    counts[line]["issues"] += 1

        result: list[dict[str, Any]] = []
        for line, value in counts.items():
            total = value["total"]
            issues = value["issues"]
            result.append(
                {
                    "production_line_id": line,
                    "total_records": total,
                    "issue_count": issues,
                    "error_rate": (issues / total) if total else 0.0,
                }
            )
        return sorted(result, key=lambda item: item["error_rate"], reverse=True)

    def get_defect_trending(
        self, start_date: date, end_date: date
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get defect trending over time (AC 3.2).

        Returns a visual breakdown of defect types (e.g., "Cosmetic" vs. "Functional")
        over the specified time period.

        Args:
            start_date: Start date for trend analysis
            end_date: End date for trend analysis

        Returns:
            Dictionary mapping defect type to list of trend data points
        """
        trend: dict[str, dict[date, int]] = defaultdict(lambda: defaultdict(int))

        for record in self.integrated_records:
            quality = record.get("quality")
            if quality is None:
                continue
            if start_date <= quality.inspection_date <= end_date:
                defect = quality.defect_type or "Unspecified"
                trend[defect][quality.inspection_date] += max(quality.defect_count, 0)

        response: dict[str, list[dict[str, Any]]] = {}
        for defect_type, points in trend.items():
            response[defect_type] = [
                {"date": point_date, "defect_count": count}
                for point_date, count in sorted(points.items())
            ]
        return response

    def search_lot_status(self, lot_code: str) -> dict[str, Any] | None:
        """
        Search for lot status (AC 3.3: Search function).

        Entering a Lot ID immediately returns its current status
        (e.g., In Production, Failed Quality, or Shipped).

        Args:
            lot_code: The lot code to search for

        Returns:
            Dictionary with lot status info or None if not found
        """
        target = lot_code.strip().upper()
        for record in self.integrated_records:
            lot: Lot | None = record.get("lot")
            if lot and lot.lot_code.strip().upper() == target:
                return {
                    "lot_code": lot.lot_code,
                    "production_date": lot.production_date,
                    "status": self.get_lot_current_status(lot),
                    "production": record.get("production"),
                    "quality": record.get("quality"),
                    "shipping": record.get("shipping"),
                }
        return None

    def get_lot_current_status(self, lot: Lot) -> str:
        """
        Get the current status of a lot.

        Possible statuses:
        - In Production
        - Pending Inspection
        - Failed Quality
        - Passed Quality
        - In Shipment
        - Shipped

        Returns:
            Current status string
        """
        if lot.has_date_conflict:
            return "Data Conflict"
        if lot.is_pending_inspection:
            return "Pending Inspection"

        linked = next(
            (record for record in self.integrated_records if record.get("lot") == lot),
            None,
        )
        if linked is None:
            return "In Production"
        quality = linked.get("quality")
        shipping = linked.get("shipping")

        if quality is None:
            return "In Production"
        if not quality.is_pass:
            return "Failed Quality"
        if shipping is None:
            return "Passed Quality"
        if shipping.shipment_status.strip().lower() == "shipped":
            return "Shipped"
        return "In Shipment"

    def get_source_health_dashboard(self) -> dict[str, dict[str, Any]]:
        """
        Get source health indicator dashboard (AC 4).

        Shows "Source Health" indicator with "Last Updated" timestamp
        for each of the three data sources (Production, Quality, Shipping).

        Returns:
            Dictionary mapping source name to health info
        """
        return dict(self.source_health)

    def get_data_integrity_dashboard(self) -> dict[str, Any]:
        """
        Get overview of all data integrity issues (AC 4).

        Returns list of:
        - Lot IDs appearing in Shipping but missing from Quality
        - Records with date conflicts (ship date before production date)
        - Lots pending inspection

        Returns:
            Dictionary with integrity issue summary
        """
        missing_quality = [
            flag["lot_code"]
            for flag in self.data_integrity_flags
            if flag.get("flag_type") == "Missing Quality" and "lot_code" in flag
        ]
        date_conflicts = [
            flag
            for flag in self.data_integrity_flags
            if flag.get("flag_type") == "Date Conflict"
        ]
        pending = [
            record.get("lot_code")
            for record in self.integrated_records
            if record.get("lot") is not None and record["lot"].is_pending_inspection
        ]
        return {
            "missing_quality_lot_ids": missing_quality,
            "date_conflicts": date_conflicts,
            "pending_inspection": pending,
            "total_flags": len(self.data_integrity_flags),
        }

    def get_weekly_error_rate_summary(self, week_start_date: date) -> dict[str, float]:
        """
        Get error rate summary by production line.

        Returns:
            Dictionary mapping line ID to error rate (0.0 to 1.0)
        """
        summary = self.get_production_health_by_line_per_week(week_start_date)
        return {item["production_line_id"]: item["error_rate"] for item in summary}

    def build_integrated_snapshot(self) -> dict[str, Any]:
        """Build a complete snapshot of the integrated data view."""
        return {
            "record_count": len(self.integrated_records),
            "source_health": self.get_source_health_dashboard(),
            "integrity": self.get_data_integrity_dashboard(),
            "records": self.integrated_records,
        }
