from pathlib import Path

from internal.analyzer import GeoAnalyzer
from internal.database import DatabaseConnector
from internal.models import SectorVertexIntersection
from pkg.config import settings


def main():
    db = DatabaseConnector(
        f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost/{settings.POSTGRES_DB}"
    )

    geojson_path = Path(__file__).parent.parent / "resources/geojson" / "UKR-ADM1_simplified.geojson"
    analyzer = GeoAnalyzer(geojson_path, db)

    grid = analyzer.generate_grid(100)
    sectors = analyzer.generate_sectors_for_squares(grid.matches, radius=100)

    for sector in sectors:
        for square in grid.matches:
            for is_intersecting, vertex in sector.check_square_vertices_intersection(square):
                if is_intersecting:
                    db.create_sector_vertex_intersection(
                        SectorVertexIntersection(sector_id=sector.id, vertex_id=vertex.id)
                    )


if __name__ == "__main__":
    main()
