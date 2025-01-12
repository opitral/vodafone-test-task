import datetime
from pathlib import Path

import folium
from folium.plugins import Fullscreen

from pkg.config import CENTER_LAT, CENTER_LON
from pkg.logger import get_logger


class GeoVisualizer:
    def __init__(self, zoom_start: int = 6):
        self.logger = get_logger(__name__)
        self.map = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=zoom_start)

    def add_borders(self, data, color: str = "blue", weight: int = 2, fill_opacity: float = 0.1):
        folium.GeoJson(
            data,
            name="Borders",
            style_function=lambda x: {
                "color": color,
                "weight": weight,
                "fillOpacity": fill_opacity,
            }
        ).add_to(self.map)

    def add_marker(self, lat: float, lon: float, popup: str, color: str = "red", icon: str = "info-sign"):
        folium.Marker(
            location=[lat, lon],
            popup=popup,
            icon=folium.Icon(color=color, icon=icon)
        ).add_to(self.map)

    def add_rectangle(self, bounds, color: str = "orange", weight: int = 2, dash_array: str = "5, 10"):
        folium.Rectangle(
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
            color=color,
            weight=weight,
            dash_array=dash_array
        ).add_to(self.map)

    def add_grid(self, data, name: str, color: str = "green", weight: float = 0.5, fill_opacity: float = 0.1):
        folium.GeoJson(
            data,
            name=name,
            style_function=lambda x: {
                "color": color,
                "weight": weight,
                "fillOpacity": fill_opacity,
            }
        ).add_to(self.map)

    def add_controls(self):
        folium.LayerControl().add_to(self.map)
        Fullscreen().add_to(self.map)

    def save(self, filename: str = None):
        if not filename:
            filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = Path(__file__).parent.parent.parent / "resources/output" / f"{filename}.html"
        self.map.save(path)
        self.logger.info(f"Map saved to {path}")
        return path

    def get_html(self):
        return self.map.render()
