import json
import math
import time
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
from shapely import Polygon, Point
from shapely.geometry import shape

from internal.database import DatabaseConnector
from internal.models import Feature, Direction, ExtremePoint, Grid, Square, Vertex, Sector
from pkg.config import CENTER_LON, CENTER_LAT, EARTH_RADIUS
from pkg.logger import get_logger

logger = get_logger(__name__)


class GeoAnalyzer:
    def __init__(self, geojson_file: Path, db: DatabaseConnector):
        self.db = db
        self._GEOJSON_FILE = geojson_file
        self._GDF = gpd.read_file(self._GEOJSON_FILE)
        self._GDF["geometry"] = self._GDF["geometry"].apply(lambda geom: geom.buffer(0) if not geom.is_valid else geom)
        self._COMBINED_AREA = self._GDF.unary_union

    @property
    def borders(self):
        return self._GDF.to_json()

    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        return self._COMBINED_AREA.bounds

    @property
    def center_point(self) -> Point:
        return Point(CENTER_LON, CENTER_LAT)

    @property
    def extreme_points(self) -> Tuple[ExtremePoint, ExtremePoint, ExtremePoint, ExtremePoint]:
        return (
            self.get_extreme_point(Direction.NORTH),
            self.get_extreme_point(Direction.SOUTH),
            self.get_extreme_point(Direction.WEST),
            self.get_extreme_point(Direction.EAST)
        )

    @property
    def features(self) -> List[Feature]:
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
            features.append(Feature(name=name, multi_polygon=shape(feature["geometry"])))

        return features

    def get_extreme_point(self, direction: Direction) -> ExtremePoint:
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

        if direction == Direction.NORTH:
            return ExtremePoint(Direction.NORTH, Point(max_lat[0], max_lat[1]))
        elif direction == Direction.SOUTH:
            return ExtremePoint(Direction.SOUTH, Point(min_lat[0], min_lat[1]))
        elif direction == Direction.WEST:
            return ExtremePoint(Direction.WEST, Point(min_lon[0], min_lon[1]))
        elif direction == Direction.EAST:
            return ExtremePoint(Direction.EAST, Point(max_lon[0], max_lon[1]))

    def generate_grid(self, grid_size: float) -> Grid:
        grid = Grid(size=grid_size)
        grid_id = self.db.create_grid(grid)
        grid_size_x, grid_size_y = grid_size / 111, grid_size / (111 / math.cos(math.radians(CENTER_LAT)))
        min_x, min_y, max_x, max_y = self._COMBINED_AREA.bounds
        x = min_x
        start = time.time()
        while x < max_x:
            y = min_y
            while y < max_y:
                a = Point(x, y)
                b = Point(x + grid_size_x, y)
                c = Point(x + grid_size_x, y + grid_size_y)
                d = Point(x, y + grid_size_y)
                square = Polygon([a, b, c, d, a])
                if square.within(self._COMBINED_AREA):
                    square_id = self.db.create_square(Square(grid_id=grid_id))
                else:
                    square_id = self.db.create_square(Square(grid_id=grid_id, is_matching=False))

                for point in [a, b, c, d]:
                    self.db.create_vertex(Vertex(square_id=square_id, point=point))

                y += grid_size_y
            x += grid_size_x
        end = time.time()
        logger.info(f"Grid generation took {end - start:.2f} seconds")
        return grid

    @staticmethod
    def _find_point_on_sphere(center: Point, azimuth: int, distance: int = 5) -> Point:
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

    def generate_sector_for_vertex(self, vertex: Vertex, azimuth: int, radius: int = 5, angle: int = 60) -> Sector:
        points = []
        half_angle = int(angle / 2)
        for offset in range(-half_angle, half_angle + 1, 1):
            point = self._find_point_on_sphere(vertex.shapely_point, azimuth + offset, radius)
            points.append(point)

        sector = Sector(
            vertex_id=vertex.id,
            azimuth=azimuth,
            radius=radius,
            angle=angle,
            polygon=Polygon([(vertex.shapely_point.x, vertex.shapely_point.y)] + points +
                            [(vertex.shapely_point.x, vertex.shapely_point.y)])
        )
        self.db.create_sector(sector)
        return sector

    def generate_sectors_for_vertex(self, vertex: Vertex, azimuths: List[int] = None,
                                    radius: int = 5, angle: int = 60) -> List[Sector]:
        if not azimuths:
            azimuths = [0, 120, 240]
        sectors = []
        for azimuth in azimuths:
            sector = self.generate_sector_for_vertex(vertex, azimuth, radius, angle)
            sectors.append(sector)
        return sectors

    def generate_sectors_for_square(self, square: Square, azimuths: List[int] = None,
                                    radius: int = 5, angle: int = 60) -> List[Sector]:

        sectors = []
        for vertex in square.vertices:
            sectors.extend(self.generate_sectors_for_vertex(vertex, azimuths, radius, angle))

        return sectors

    def generate_sectors_for_squares(self, squares: List[Square], azimuths: List[int] = None,
                                     radius: int = 5, angle: int = 60) -> List[Sector]:
        sectors = []
        start = time.time()
        for square in squares:
            sectors.extend(self.generate_sectors_for_square(square, azimuths, radius, angle))
        end = time.time()
        logger.info(f"Sectors generation took {end - start:.2f} seconds")
        return sectors
