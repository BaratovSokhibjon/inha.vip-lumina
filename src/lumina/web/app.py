"""
Lumina Dashboard

Streamlit web interface for monitoring and controlling Lumina.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from lumina.core.main import LuminaApp

st.set_page_config(
    page_title="Lumina Dashboard",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)


class LuminaDashboard:
    """Main dashboard class"""

    def __init__(self, app: LuminaApp):
        self.app = app

    def render(self):
        """Render the dashboard"""
        st.title("💡 Lumina Dashboard")

        # Sidebar
        st.sidebar.title("Lumina")
        page = st.sidebar.selectbox("Navigate", ["Controls", "Environment", "ML", "System"])

        # Main content
        if page == "Controls":
            self.render_controls()
        elif page == "Environment":
            self.render_environment()
        elif page == "ML":
            self.render_ml()
        elif page == "System":
            self.render_system()

    def render_controls(self):
        """Render lamp controls"""
        st.header("Controls")
        status = self.app.lamp_controller.get_status()["lamp"]

        # Power
        if st.button("Turn Off" if status["is_on"] else "Turn On"):
            if status["is_on"]:
                self.app.lamp_controller.turn_off()
            else:
                self.app.lamp_controller.turn_on()

        # Brightness
        brightness = st.slider("Brightness", 0, 100, status["current_brightness"])
        if brightness != status["current_brightness"]:
            self.app.lamp_controller.set_brightness(brightness)

        # Color
        color_hex = '#%02x%02x%02x' % status["current_color"]
        new_color_hex = st.color_picker("Color", color_hex)
        if new_color_hex != color_hex:
            r, g, b = tuple(int(new_color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            self.app.lamp_controller.set_color(r, g, b)

    def render_environment(self):
        """Render environmental data"""
        st.header("Environment")
        sensor_data = self.app.lamp_controller.sensors.get_all_data()

        st.subheader("Weather")
        st.write(sensor_data["weather"])

        st.subheader("Air Quality")
        st.write(sensor_data["air_quality"])

        st.subheader("Earthquakes")
        st.write(sensor_data["earthquake"])

    def render_ml(self):
        """Render ML data"""
        st.header("Machine Learning")
        ml_status = self.app.lamp_controller.ml.get_status()
        st.write(ml_status)

    def render_system(self):
        """Render system data"""
        st.header("System")
        system_info = self.app.lamp_controller.utils.get_system_info()
        st.write(system_info)


if __name__ == "__main__":
    # This is a placeholder for running the app. The actual app is run from the CLI.
    st.title("Lumina Dashboard")
    st.write("This is a placeholder for the Lumina web dashboard.")
    st.write("To run the full application, use the `lumina run` command.")
