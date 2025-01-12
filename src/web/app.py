import os
from pathlib import Path

from flask import Flask, request, render_template, send_from_directory

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
        visualizer.add_borders(analyzer.geojson_file)

    if bounding_box_enabled:
        visualizer.add_rectangle(analyzer.bounds)

    if center_marker_enabled:
        visualizer.add_marker(CENTER_LAT, CENTER_LON, "Center point")

    if extreme_points_enabled:
        extreme_points = analyzer.get_extreme_points()
        visualizer.add_marker(
            extreme_points["north"][0], extreme_points["north"][1], "Northernmost point", color="blue"
        )
        visualizer.add_marker(
            extreme_points["south"][0], extreme_points["south"][1], "Southernmost point", color="blue"
        )
        visualizer.add_marker(
            extreme_points["west"][0], extreme_points["west"][1], "Westernmost point", color="blue"
        )
        visualizer.add_marker(
            extreme_points["east"][0], extreme_points["east"][1], "Easternmost point", color="blue"
        )

    matching_grid, not_mathing_grid = analyzer.generate_grid(grid_size)
    visualizer.add_grid(matching_grid, "Matching grid")
    if not_matching_grid_enabled:
        visualizer.add_grid(not_mathing_grid, "Not matching grid", color="red")

    visualizer.add_controls()
    map_path = visualizer.save()
    return send_from_directory(Path(map_path).parent, Path(map_path).name)


if __name__ == "__main__":
    app.run(debug=True)
