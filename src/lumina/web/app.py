"""
Lumina Dashboard

Streamlit web interface for monitoring and controlling Lumina.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from lumina.database.database import DatabaseManager
from lumina.utils.config import load_config

st.set_page_config(
    page_title="Lumina Dashboard",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)


class LuminaDashboard:
    """Main dashboard class"""

    def __init__(self):
        self.config = load_config()
        self.db = DatabaseManager(self.config)

    def render(self):
        """Render the dashboard"""
        st.title("💡 Lumina Dashboard")

        # Sidebar
        st.sidebar.title("Lumina")
        page = st.sidebar.selectbox("Navigate", ["Overview", "Controls", "History", "Environment", "System"])

        # Main content
        if page == "Overview":
            self.render_overview()
        elif page == "Controls":
            self.render_controls()
        elif page == "History":
            self.render_history()
        elif page == "Environment":
            self.render_environment()
        elif page == "System":
            self.render_system()

    def render_overview(self):
        """Render overview dashboard"""
        st.header("System Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Status", "Running", "🟢 Online")

        with col2:
            st.metric("Uptime", "Active", "Simulation Mode")

        with col3:
            st.metric("Database", "Connected", "SQLite")

        st.subheader("Recent Activity")
        st.info("Lumina smart lamp system is running in simulation mode")
        st.info("Brightness control and environmental monitoring active")
        st.info("Web dashboard connected to database")

    def render_controls(self):
        """Render manual controls"""
        st.header("Lamp Controls")

        st.subheader("Brightness Control")
        st.write("Adjust the lamp brightness (simulation mode)")

        # Get current brightness from database or use default
        try:
            stats = self.db.get_stats()
            current_brightness = stats.get('avg_brightness', 50) if stats else 50
        except:
            current_brightness = 50

        # Brightness slider
        brightness = st.slider(
            "Brightness",
            min_value=0,
            max_value=100,
            value=int(current_brightness),
            step=5,
            help="Adjust lamp brightness (0-100%)"
        )

        if st.button("Apply Brightness", type="primary"):
            st.success(f"Brightness set to {brightness}%")
            # In a real implementation, this would send command to the lamp
            # For now, just show the change

        st.divider()

        st.subheader("Color Control")
        st.write("Select lamp color (simulation mode)")

        # Color picker
        color = st.color_picker("Choose Color", "#FFFFFF", help="Select lamp color")

        if st.button("Apply Color", type="primary"):
            st.success(f"Color set to {color}")
            # In a real implementation, this would change the lamp color

        st.divider()

        st.subheader("Power Control")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Turn ON", type="primary"):
                st.success("Lamp turned ON")

        with col2:
            if st.button("Turn OFF", type="secondary"):
                st.success("Lamp turned OFF")

        st.divider()

        st.subheader("Mode Control")
        mode = st.radio(
            "Lamp Mode",
            ["Manual", "Auto"],
            help="Manual: Direct control, Auto: Environmental response"
        )

        if st.button("Apply Mode"):
            st.success(f"Mode set to {mode}")

    def render_history(self):
        """Render user interaction history"""
        st.header("User Interaction History")

        try:
            # Get stats from database
            stats = self.db.get_stats()

            if stats:
                st.subheader("Database Statistics")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Interactions", stats.get('total_interactions', 0))

                with col2:
                    st.metric("Active Days", stats.get('active_days', 0))

                with col3:
                    st.metric("Avg Brightness", f"{stats.get('avg_brightness', 0):.1f}%")

                # Show recent patterns
                patterns = self.db.get_user_patterns(days=7)
                if patterns:
                    st.subheader("Recent Patterns")
                    for pattern in patterns[:5]:  # Show last 5
                        st.write(f"• {pattern.get('hour', 0):02d}:00 - Brightness: {pattern.get('avg_brightness', 0):.1f}%")
                else:
                    st.info("No pattern data available yet")
            else:
                st.info("No data available yet")

        except Exception as e:
            st.error(f"Error loading history: {e}")
            st.info("Database may not be initialized yet")

    def render_environment(self):
        """Render environmental data"""
        st.header("Environmental Monitoring")

        st.subheader("Earthquake Monitoring")
        st.info("✅ Active - Monitoring significant earthquakes worldwide")
        st.write("Last check: Recent earthquakes fetched from USGS API")

        st.subheader("Weather & Air Quality")
        st.warning("⚠️ API keys required for full functionality")
        st.write("WeatherAPI.com and WAQI keys needed for real-time data")

        # Mock data for demo
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Mock Temperature", "22°C", "Sunny")
        with col2:
            st.metric("Mock Air Quality", "Good", "AQI: 25")

    def render_system(self):
        """Render system information"""
        st.header("System Information")

        st.subheader("Configuration")
        st.json({
            "Mode": "Simulation",
            "Database": self.config.get("system", {}).get("database_path", "data/storage.db"),
            "Log Level": self.config.get("system", {}).get("log_level", "INFO"),
            "Web Port": self.config.get("web", {}).get("port", 8501)
        })

        st.subheader("Hardware Status")
        st.success("✅ Hardware simulation active")
        st.success("✅ LED strip simulation running")
        st.success("✅ Sensor monitoring active")


if __name__ == "__main__":
    # Create dashboard instance
    dashboard = LuminaDashboard()
    dashboard.render()
