import os
from pathlib import Path

from flask import Flask, request, render_template, send_from_directory

from internal.analyzer import GeoAnalyzer
from internal.database import DatabaseConnector
from internal.visualizer import GeoVisualizer
from pkg.config import settings

app = Flask(__name__)
db = DatabaseConnector(
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost/{settings.POSTGRES_DB}"
)


@app.route('/')
def index():
    geojson_dir_path = Path(__file__).parent.parent.parent / "resources/geojson"
    geojson_files = [f.replace(".geojson", "") for f in os.listdir(geojson_dir_path) if f.endswith(".geojson")]
    return render_template("index.html", geojson_files=geojson_files)


@app.route("/map", methods=["GET"])
def generate_map():
    geojson_file_name = request.args.get("geojson")
    grid_size = int(request.args.get("gridSize"))
    sector_radius = int(request.args.get("sectorRadius"))

    analyzer = GeoAnalyzer(Path(__file__).parent.parent.parent / "resources/geojson" / geojson_file_name, db)
    visualizer = GeoVisualizer()

    grid = analyzer.generate_grid(grid_size)
    sectors = analyzer.generate_sectors_for_squares(grid.matches, radius=sector_radius)

    visualizer.add_borders(analyzer.borders)
    visualizer.add_bounds(analyzer.bounds)
    visualizer.add_center_point(analyzer.center_point)
    visualizer.add_extreme_points(analyzer.extreme_points)
    visualizer.add_grid(grid.matches)
    visualizer.add_grid(grid.not_matches, color="red")
    visualizer.add_sectors(sectors)
    visualizer.add_controls()
    map_path = visualizer.save()

    return send_from_directory(Path(map_path).parent, Path(map_path).name)


if __name__ == "__main__":
    app.run(port=5000)
