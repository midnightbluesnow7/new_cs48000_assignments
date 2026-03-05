"""Reusable UI widgets for the dashboard."""

from typing import Any

import pandas as pd
import streamlit as st


class ProductionHealthWidget:
    """Widget for displaying production health metrics."""

    @staticmethod
    def render_error_rate_by_line(data: list[dict[str, Any]]) -> None:
        """
        Render production line error rates.

        (AC 3.1: Which production lines have highest error rates per week)

        Args:
            data: List of line health records
        """
        if not data:
            st.info("No production health data available for this range.")
            return
        frame = pd.DataFrame(data)
        st.subheader("Error Rate by Production Line")
        st.bar_chart(frame.set_index("production_line_id")["error_rate"])

    @staticmethod
    def render_error_trend_chart(data: list[dict[str, Any]]) -> None:
        """Render error trend chart over time."""
        if not data:
            return
        frame = pd.DataFrame(data)
        if "error_rate" in frame:
            st.line_chart(frame[["error_rate"]])

    @staticmethod
    def render_line_comparison_table(data: list[dict[str, Any]]) -> None:
        """Render table comparing all production lines."""
        if not data:
            return
        st.dataframe(pd.DataFrame(data), use_container_width=True)


class DefectTrendingWidget:
    """Widget for displaying defect trending analysis."""

    @staticmethod
    def render_defect_by_type(data: dict[str, list[dict[str, Any]]]) -> None:
        """
        Render visual breakdown of defect types over time.

        (AC 3.2: Visual breakdown of defect types (Cosmetic vs Functional) over time)

        Args:
            data: Dictionary mapping defect type to trend data
        """
        if not data:
            st.info("No defect data available.")
            return
        rows: list[dict[str, Any]] = []
        for defect_type, points in data.items():
            for point in points:
                rows.append(
                    {
                        "defect_type": defect_type,
                        "date": point["date"],
                        "defect_count": point["defect_count"],
                    }
                )
        frame = pd.DataFrame(rows)
        st.subheader("Defect Trend")
        st.dataframe(frame, use_container_width=True)

    @staticmethod
    def render_defect_distribution_pie(data: dict[str, int]) -> None:
        """Render pie chart of defect type distribution."""
        if not data:
            return
        frame = pd.DataFrame(
            [{"defect_type": key, "count": value} for key, value in data.items()]
        )
        st.bar_chart(frame.set_index("defect_type")["count"])

    @staticmethod
    def render_defect_timeline(data: dict[str, list[dict[str, Any]]]) -> None:
        """Render timeline of defects over period."""
        if not data:
            return
        flattened: list[dict[str, Any]] = []
        for defect_type, points in data.items():
            for point in points:
                flattened.append(
                    {
                        "date": point["date"],
                        "defect_count": point["defect_count"],
                        "defect_type": defect_type,
                    }
                )
        frame = pd.DataFrame(flattened)
        st.line_chart(frame.set_index("date")["defect_count"])


class ShipmentSearchWidget:
    """Widget for searching and displaying shipment status."""

    @staticmethod
    def render_search_box() -> str:
        """
        Render lot ID search box.

        (AC 3.3: Search function where entering Lot ID returns current status)

        Returns:
            The search query (lot ID) entered by user
        """
        return str(st.text_input("Enter Lot ID", placeholder="LOT-20251219-003"))

    @staticmethod
    def render_lot_status_result(lot_data: dict[str, Any]) -> None:
        """
        Render search result showing lot status.

        Returns status like: In Production, Failed Quality, or Shipped

        Args:
            lot_data: Dictionary with lot information
        """
        if not lot_data:
            st.warning("No lot found.")
            return
        st.success(f"Status: {lot_data['status']}")
        st.json(
            {
                "lot_code": lot_data.get("lot_code"),
                "production_date": str(lot_data.get("production_date")),
                "status": lot_data.get("status"),
            }
        )

    @staticmethod
    def render_lot_timeline(lot_id: str) -> None:
        """Render timeline of lot through production, quality, and shipping."""
        st.caption(f"Timeline for {lot_id}")


class SourceHealthWidget:
    """Widget for displaying data source health."""

    @staticmethod
    def render_source_health_dashboard(health_data: dict[str, dict[str, Any]]) -> None:
        """
        Render Source Health indicator dashboard.

        (AC 4: Simple Source Health indicator showing Last Updated timestamp
        for each of three spreadsheets)

        Args:
            health_data: Dictionary mapping source name to health info
        """
        if not health_data:
            st.info("No source health data available.")
            return
        for source_name, details in health_data.items():
            SourceHealthWidget.render_health_indicator(
                source_name,
                details.get("status", "Unknown"),
                str(details.get("last_updated", "N/A")),
            )

    @staticmethod
    def render_health_indicator(
        source_name: str, status: str, last_updated: str
    ) -> None:
        """Render individual source health indicator."""
        st.write(f"**{source_name}**: {status} (Last updated: {last_updated})")

    @staticmethod
    def render_refresh_status(status_info: str) -> None:
        """Render refresh status and timestamp information."""
        st.caption(status_info)


class DataIntegrityWidget:
    """Widget for displaying data integrity issues."""

    @staticmethod
    def render_integrity_summary(integrity_data: dict[str, Any]) -> None:
        """
        Render summary of data integrity issues.

        (AC 4: Highlight Lot IDs appearing in Shipping but missing from Quality,
        and records with ship date before production date)

        Args:
            integrity_data: Dictionary with integrity issue summary
        """
        st.metric("Total Flags", integrity_data.get("total_flags", 0))
        DataIntegrityWidget.render_missing_quality_flags(
            integrity_data.get("missing_quality_lot_ids", [])
        )
        DataIntegrityWidget.render_date_conflict_flags(
            integrity_data.get("date_conflicts", [])
        )

    @staticmethod
    def render_missing_quality_flags(lot_ids: list[str]) -> None:
        """Render list of lots with missing quality records."""
        if lot_ids:
            st.warning(f"Missing quality records: {', '.join(lot_ids)}")

    @staticmethod
    def render_date_conflict_flags(conflicts: list[dict[str, Any]]) -> None:
        """Render list of date conflicts."""
        if conflicts:
            st.error("Date conflicts detected")
            st.dataframe(pd.DataFrame(conflicts), use_container_width=True)

    @staticmethod
    def render_integrity_issues_table(issues: list[dict[str, Any]]) -> None:
        """Render table of all integrity issues."""
        if issues:
            st.dataframe(pd.DataFrame(issues), use_container_width=True)


class LoadingWidget:
    """Widget for showing loading states."""

    @staticmethod
    def show_loading_spinner(message: str = "Loading...") -> None:
        """Show loading spinner with message."""
        st.spinner(message)

    @staticmethod
    def show_progress_bar(progress: float) -> None:
        """Show progress bar (0.0 to 1.0)."""
        st.progress(min(max(progress, 0.0), 1.0))
