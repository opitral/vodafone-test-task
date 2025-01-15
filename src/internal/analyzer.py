import json
import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
from shapely import Polygon, Point
from shapely.geometry import shape
from shapely.geometry.base import BaseGeometry

from pkg.config import CENTER_LAT, EARTH_RADIUS


@dataclass
class Feature:
    name: str
    geom: BaseGeometry

    def __repr__(self):
        return f"Feature(name={self.name})"


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    WEST = "west"
    EAST = "east"


@dataclass
class ExtremePoint:
    direction: Direction
    point: Point


@dataclass
class Grid:
    matches: List[Polygon]
    not_matches: List[Polygon]


class GeoAnalyzer:
    def __init__(self, geojson_file: Path):
        self._GEOJSON_FILE = geojson_file
        self._GDF = gpd.read_file(self._GEOJSON_FILE)
        self._GDF["geometry"] = self._GDF["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
        self._COMBINED_AREA = self._GDF.unary_union

    @property
    def geojson_file(self) -> str:
        return str(self._GEOJSON_FILE)

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return self._COMBINED_AREA.bounds

    def get_features(self) -> List[Feature]:
        with open(self._GEOJSON_FILE, "r", encoding="utf-8") as file:
            geojson_data = json.load(file)

        features = []
        for feature in geojson_data["features"]:
            properties: dict = feature.get("properties")
            name = None
            if properties:
                for key in properties.keys():
                    if "name" in key.lower():
                        name = properties.get(key)
                        break
            features.append(Feature(name=name, geom=shape(feature["geometry"])))

        return features

    def get_extreme_points(self) -> Tuple[ExtremePoint, ExtremePoint, ExtremePoint, ExtremePoint]:
        if self._COMBINED_AREA.geom_type == "MultiPolygon":
            polygons = list(self._COMBINED_AREA.geoms)
        else:
            polygons = [self._COMBINED_AREA]

        all_coords = []
        for polygon in polygons:
            if polygon.exterior:
                all_coords.extend(list(polygon.exterior.coords))

        max_lat = max(all_coords, key=lambda x: x[1])
        min_lat = min(all_coords, key=lambda x: x[1])
        max_lon = max(all_coords, key=lambda x: x[0])
        min_lon = min(all_coords, key=lambda x: x[0])

        return (
            ExtremePoint(Direction.NORTH, Point(max_lat[0], max_lat[1])),
            ExtremePoint(Direction.SOUTH, Point(min_lat[0], min_lat[1])),
            ExtremePoint(Direction.WEST, Point(min_lon[0], min_lon[1])),
            ExtremePoint(Direction.EAST, Point(max_lon[0], max_lon[1]))
        )

    def generate_grid(self, grid_size: float) -> Grid:
        grid_size_x, grid_size_y = grid_size / 111, grid_size / (111 / math.cos(math.radians(CENTER_LAT)))
        min_x, min_y, max_x, max_y = self._COMBINED_AREA.bounds
        matching_squares = []
        not_matching_squares = []
        x = min_x
        while x < max_x:
            y = min_y
            while y < max_y:
                square = Polygon([
                    (x, y),
                    (x + grid_size_x, y),
                    (x + grid_size_x, y + grid_size_y),
                    (x, y + grid_size_y),
                    (x, y)
                ])
                if square.within(self._COMBINED_AREA):
                    matching_squares.append(square)
                else:
                    not_matching_squares.append(square)
                y += grid_size_y
            x += grid_size_x

        return Grid(matches=matching_squares, not_matches=not_matching_squares)

    @staticmethod
    def find_point_on_sphere(center: Point, azimuth: int, distance: int = 5) -> Point:
        lat1 = math.radians(center.y)
        lon1 = math.radians(center.x)
        azimuth = math.radians(azimuth)

        delta = distance / EARTH_RADIUS

        lat2 = math.asin(math.sin(lat1) * math.cos(delta) +
                         math.cos(lat1) * math.sin(delta) * math.cos(azimuth))

        lon2 = lon1 + math.atan2(math.sin(azimuth) * math.sin(delta) * math.cos(lat1),
                                 math.cos(delta) - math.sin(lat1) * math.sin(lat2))

        lat2 = math.degrees(lat2)
        lon2 = math.degrees(lon2)

        lon2 = (lon2 + 180) % 360 - 180

        return Point(lon2, lat2)

    def generate_sector(self, center: Point, azimuth: int, radius: int = 5, angle: int = 60) -> Polygon:
        points = []
        for offset in range(-int(angle/2), int(angle/2) + 1, 1):
            point = self.find_point_on_sphere(center, azimuth + offset, radius)
            points.append(point)

        return Polygon([(center.x, center.y)] + points + [(center.x, center.y)])
