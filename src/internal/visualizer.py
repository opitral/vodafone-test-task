import datetime
import random
from pathlib import Path
from typing import List, Tuple

import folium
from folium.plugins import Fullscreen
from shapely import Point

from internal.models import Square, ExtremePoint, Direction, Sector
from pkg.config import CENTER_LAT, CENTER_LON
from pkg.logger import get_logger

logger = get_logger(__name__)


class GeoVisualizer:
    def __init__(self, zoom_start: int = 6):
        self.map = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=zoom_start)
        folium.TileLayer(
            tiles="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.{ext}",
            attr='&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; '
                 '<a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; '
                 '<a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            name="Smooth Dark",
            overlay=False,
            control=True,
            min_zoom=0,
            max_zoom=20,
            ext="png"
        ).add_to(self.map)

    def add_grid(self, grid: List[Square], color: str = "green"):
        group = folium.FeatureGroup(name=color.capitalize() + " grid", show=color == "green")
        for square in grid:
            coords = [(c[1], c[0]) for c in square.shapely_polygon.exterior.coords]
            folium.Polygon(
                locations=coords,
                color=color,
                weight=1
            ).add_to(group)
        group.add_to(self.map)

    def add_extreme_points(self, extreme_points: Tuple[ExtremePoint, ExtremePoint, ExtremePoint, ExtremePoint]):
        group = folium.FeatureGroup(name="Extreme points", show=False)
        for extreme_point in extreme_points:
            if extreme_point.direction == Direction.NORTH:
                angle = 0
            elif extreme_point.direction == Direction.SOUTH:
                angle = 180
            elif extreme_point.direction == Direction.WEST:
                angle = 270
            else:
                angle = 90
            folium.Marker(
                location=[extreme_point.point.y, extreme_point.point.x],
                popup=extreme_point.direction.value.capitalize() + " extreme point",
                icon=folium.Icon(color="blue", icon="arrow-up", angle=angle)
            ).add_to(group)
        group.add_to(self.map)

    def add_center_point(self, center: Point):
        group = folium.FeatureGroup(name="Center point", show=False)
        folium.Marker(
            location=[center.y, center.x],
            popup="Center",
            icon=folium.Icon(color="pink", icon="info-sign")
        ).add_to(group)
        group.add_to(self.map)

    def add_bounds(self, bounds: Tuple[float, float, float, float]):
        group = folium.FeatureGroup(name="Bounds", show=False)
        folium.Rectangle(
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
            color="white",
            weight=2,
            dash_array="5, 10"
        ).add_to(group)
        group.add_to(self.map)

    def add_borders(self, borders: dict):
        folium.GeoJson(
            data=borders,
            name="Borders",
            style_function=lambda x: {
                "color": "purple",
                "weight": 1,
                "fillOpacity": 0.1,
            }
        ).add_to(self.map)

    def add_sectors(self, sectors: List[Sector]):
        group = folium.FeatureGroup(name="Sectors", show=True)
        for sector in sectors:
            folium.Polygon(
                locations=[(c[1], c[0]) for c in sector.shapely_polygon.exterior.coords],
                color=random.choice(["red", "green", "blue", "yellow", "orange", "purple", "pink"]),
                weight=1,
                fill_opacity=0.5
            ).add_to(group)
        group.add_to(self.map)

    def add_controls(self):
        folium.LayerControl().add_to(self.map)
        Fullscreen().add_to(self.map)

    def save(self, filename: str = None):
        if not filename:
            filename = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = Path(__file__).parent.parent.parent / "resources/output" / f"{filename}.html"
        self.map.save(path)
        logger.info(f"Map saved to {path}")
        return path
