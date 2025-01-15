import os
import random
from pathlib import Path

import geopandas as gpd
from flask import Flask, request, render_template, send_from_directory
from shapely import Point

from internal.analyzer import GeoAnalyzer
from internal.visualizer import GeoVisualizer
from pkg.config import CENTER_LAT, CENTER_LON

app = Flask(__name__)


@app.route('/')
def index():
    geojson_dir_path = Path(__file__).parent.parent.parent / "resources/geojson"
    geojson_files = [f.replace(".geojson", "") for f in os.listdir(geojson_dir_path) if f.endswith(".geojson")]
    return render_template("index.html", geojson_files=geojson_files)


@app.route('/map', methods=["POST"])
def generate_map():
    geojson_name = request.form.get("geojsonSelect")
    borders_enabled = request.form.get("bordersCheckbox") == "on"
    bounding_box_enabled = request.form.get("boundingBoxCheckbox") == "on"
    center_marker_enabled = request.form.get("centerPointCheckbox") == "on"
    extreme_points_enabled = request.form.get("extremePointsCheckbox") == "on"
    grid_size = int(request.form.get("gridSizeInput"))
    not_matching_grid_enabled = request.form.get("notMatchingGridCheckbox") == "on"

    analyzer = GeoAnalyzer(Path(__file__).parent.parent.parent / "resources/geojson" / geojson_name)
    visualizer = GeoVisualizer()

    if borders_enabled:
        visualizer.add_polygon(analyzer.geojson_file, "Borders of the Ukraine")

    if bounding_box_enabled:
        visualizer.add_rectangle(analyzer.bounds)

    if center_marker_enabled:
        visualizer.add_point(Point(CENTER_LON, CENTER_LAT), "Center point")

    if extreme_points_enabled:
        extreme_points = analyzer.get_extreme_points()
        for point in extreme_points:
            visualizer.add_point(point.point, point.direction.value.capitalize() + "ern most point")

    grid = analyzer.generate_grid(grid_size)
    matching_grid = gpd.GeoDataFrame({"geometry": grid.matches}, crs="EPSG:4326")
    not_matching_grid = gpd.GeoDataFrame({"geometry": grid.not_matches}, crs="EPSG:4326")
    visualizer.add_polygon(matching_grid, "Matching grid")
    if not_matching_grid_enabled:
        visualizer.add_polygon(not_matching_grid, "Not matching grid", color="red")

    for square in grid.matches:
        minx, miny, maxx, maxy = square.bounds
        for point in [(minx, miny), (minx, maxy), (maxx, miny), (maxx, maxy)]:
            for azimuth in [0, 120, 240]:
                sector = analyzer.generate_sector(Point(*point), azimuth, radius=50)
                visualizer.add_polygon(
                    sector,
                    f"Sector from {point} with {azimuth}°",
                    color=random.choice(["blue", "green", "yellow", "purple", "orange", "pink", "brown"])
                )

    visualizer.add_controls()
    map_path = visualizer.save()
    return send_from_directory(Path(map_path).parent, Path(map_path).name)


if __name__ == "__main__":
    app.run(debug=True)
