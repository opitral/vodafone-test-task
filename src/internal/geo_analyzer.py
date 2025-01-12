import json
import math
from pathlib import Path
from typing import List, Tuple, Dict
import geopandas as gpd
from shapely import Polygon


class GeoAnalyzer:
    def __init__(self, geojson_file: Path, center_lat: float = None, center_lon: float = None):
        self._GEOJSON_FILE = geojson_file

        self._GDF = gpd.read_file(self._GEOJSON_FILE)
        self._GDF["geometry"] = self._GDF["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
        self._COMBINED_AREA = self._GDF.unary_union

        if center_lat and center_lon:
            self._CENTER_LAT, self._CENTER_LON = center_lat, center_lon
        else:
            self._CENTER_LAT, self._CENTER_LON = self._COMBINED_AREA.centroid.y, self._COMBINED_AREA.centroid.x

    @property
    def geojson_file(self) -> str:
        return str(self._GEOJSON_FILE)

    @property
    def center_lat(self) -> float:
        return self._CENTER_LAT

    @property
    def center_lon(self) -> float:
        return self._CENTER_LON

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

    def get_extreme_points(self) -> Dict[str, Dict[str, float]]:
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
            "north": {"lat": max_lat[1], "lon": max_lat[0]},
            "south": {"lat": min_lat[1], "lon": min_lat[0]},
            "west": {"lat": min_lon[1], "lon": min_lon[0]},
            "east": {"lat": max_lon[1], "lon": max_lon[0]},
        }

    def generate_grid(self, grid_size: float, generate_not_matching: bool = False) -> (
            Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame] | gpd.GeoDataFrame):
        grid_size_x, grid_size_y = grid_size / 111, grid_size / (111 / math.cos(math.radians(self._CENTER_LAT)))
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
                elif generate_not_matching:
                    not_matching_squares.append(square)
                y += grid_size_y
            x += grid_size_x

        if not_matching_squares:
            matching_grid_gdf = gpd.GeoDataFrame({"geometry": matching_squares}, crs="EPSG:4326")
            not_matching_grid_gdf = gpd.GeoDataFrame({"geometry": not_matching_squares}, crs="EPSG:4326")
            return matching_grid_gdf, not_matching_grid_gdf

        else:
            matching_grid_gdf = gpd.GeoDataFrame({"geometry": matching_squares}, crs="EPSG:4326")
            return matching_grid_gdf
