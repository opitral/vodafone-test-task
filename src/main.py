from pathlib import Path

from internal.analyzer import GeoAnalyzer
from internal.database import DatabaseConnector
from internal.visualizer import GeoVisualizer
from pkg.config import settings

db = DatabaseConnector(
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost/{settings.POSTGRES_DB}"
)


def main():
    geojson_path = Path(__file__).parent.parent / "resources/geojson" / "UKR-ADM1_simplified.geojson"
    analyzer = GeoAnalyzer(geojson_path)
    visualizer = GeoVisualizer()

    extreme_point = analyzer.get_extreme_points()
    for point in extreme_point:
        visualizer.add_point(point.point, point.direction.value.capitalize() + "ern most point")

    visualizer.save()


if __name__ == "__main__":
    main()
