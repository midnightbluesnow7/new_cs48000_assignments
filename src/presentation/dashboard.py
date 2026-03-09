"""Streamlit Dashboard - Main UI application."""

import logging
from datetime import date
from typing import cast

import streamlit as st

from src.presentation.widgets import (
    DataIntegrityWidget,
    DefectTrendingWidget,
    ProductionHealthWidget,
    ShipmentSearchWidget,
    SourceHealthWidget,
)
from src.services.integrated_view_service import IntegratedViewService

logger = logging.getLogger(__name__)


class Dashboard:
    """Main Streamlit dashboard for Operations Data Hub."""

    def __init__(self) -> None:
        """Initialize the dashboard."""
        self.integrated_view_service = IntegratedViewService(
            integrated_records=st.session_state.get("integrated_records", []),
            data_integrity_flags=st.session_state.get("integrity_flags", []),
            source_health=st.session_state.get("source_health", {}),
        )
        if "date_range" not in st.session_state:
            today = date.today()
            st.session_state["date_range"] = (today, today)

    def run(self) -> None:
        """Run the main dashboard application."""
        st.set_page_config(page_title="SteelWorks Operations Data Hub", layout="wide")
        self.render_header()
        self.setup_sidebar()
        selected_page = self.render_navigation()

        if selected_page == "Production Health":
            self.render_production_health_page()
        elif selected_page == "Defect Trending":
            self.render_defect_trending_page()
        elif selected_page == "Shipment Search":
            self.render_shipment_search_page()
        elif selected_page == "Source Health":
            self.render_source_health_page()
        elif selected_page == "Data Integrity":
            self.render_data_integrity_page()

    def render_header(self) -> None:
        """Render dashboard header and title."""
        st.title("SteelWorks Operations Data Hub")
        st.caption("Integrated production, quality, and shipping analytics")

    def render_navigation(self) -> str:
        """
        Render navigation menu.

        Returns:
            Selected page/tab name
        """
        return str(
            st.radio(
                "Navigation",
                [
                    "Production Health",
                    "Defect Trending",
                    "Shipment Search",
                    "Source Health",
                    "Data Integrity",
                ],
                horizontal=True,
            )
        )

    def render_production_health_page(self) -> None:
        """Render Production Health page (AC 3.1)."""
        start_date, _ = self.get_selected_date_range()
        health_data = (
            self.integrated_view_service.get_production_health_by_line_per_week(
                start_date
            )
        )
        ProductionHealthWidget.render_error_rate_by_line(health_data)
        ProductionHealthWidget.render_line_comparison_table(health_data)

    def render_defect_trending_page(self) -> None:
        """Render Defect Trending page (AC 3.2)."""
        logger.info("User opened the Recurring Defects page")
        start_date, end_date = self.get_selected_date_range()
        defect_data = self.integrated_view_service.get_defect_trending(
            start_date, end_date
        )
        DefectTrendingWidget.render_defect_by_type(defect_data)
        total_by_type = {
            defect_type: sum(point["defect_count"] for point in points)
            for defect_type, points in defect_data.items()
        }
        DefectTrendingWidget.render_defect_distribution_pie(total_by_type)

    def render_shipment_search_page(self) -> None:
        """Render Shipment Search & Status page (AC 3.3)."""
        query = ShipmentSearchWidget.render_search_box()
        if query:
            lot_data = self.integrated_view_service.search_lot_status(query)
            ShipmentSearchWidget.render_lot_status_result(lot_data or {})

    def render_source_health_page(self) -> None:
        """Render Data Source Health Dashboard (AC 4)."""
        health = self.integrated_view_service.get_source_health_dashboard()
        SourceHealthWidget.render_source_health_dashboard(health)

    def render_data_integrity_page(self) -> None:
        """Render Data Integrity Issues page (AC 4)."""
        integrity = self.integrated_view_service.get_data_integrity_dashboard()
        DataIntegrityWidget.render_integrity_summary(integrity)

    def handle_page_load(self) -> None:
        """Handle automatic data refresh on page load (AC 1)."""
        return None

    def setup_sidebar(self) -> None:
        """Setup sidebar with filters and controls."""
        st.sidebar.header("Filters")
        start_date = st.sidebar.date_input(
            "Start Date", value=st.session_state["date_range"][0]
        )
        end_date = st.sidebar.date_input(
            "End Date", value=st.session_state["date_range"][1]
        )
        st.session_state["date_range"] = (start_date, end_date)

    def get_selected_date_range(self) -> tuple[date, date]:
        """
        Get selected date range from sidebar.

        Returns:
            Tuple of (start_date, end_date)
        """
        return cast(
            tuple[date, date],
            st.session_state.get("date_range", (date.today(), date.today())),
        )

    def show_error_message(self, message: str) -> None:
        """Display error message to user."""
        st.error(message)

    def show_success_message(self, message: str) -> None:
        """Display success message to user."""
        st.success(message)

    def show_warning_message(self, message: str) -> None:
        """Display warning message to user."""
        st.warning(message)
