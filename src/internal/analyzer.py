import json
import math
from pathlib import Path
from typing import List, Tuple, Dict

import geopandas as gpd
from shapely import Polygon

from pkg.config import CENTER_LAT


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

    def get_features(self) -> List[Tuple[str, Dict]]:
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
            features.append((name, feature["geometry"]))

        return features

    def get_extreme_points(self) -> Dict[str, Tuple[float, float]]:
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

        return {
            "north": (max_lat[1], max_lat[0]),
            "south": (min_lat[1], min_lat[0]),
            "west": (min_lon[1], min_lon[0]),
            "east": (max_lon[1], max_lon[0]),
        }

    def generate_grid(self, grid_size: float) -> (
            Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame] | gpd.GeoDataFrame):
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

        matching_grid_gdf = gpd.GeoDataFrame({"geometry": matching_squares}, crs="EPSG:4326")
        not_matching_grid_gdf = gpd.GeoDataFrame({"geometry": not_matching_squares}, crs="EPSG:4326")
        return matching_grid_gdf, not_matching_grid_gdf
