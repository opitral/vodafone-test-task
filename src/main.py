from pathlib import Path

from internal.analyzer import GeoAnalyzer
from internal.database import DatabaseConnector
from pkg.config import settings
from pkg.logger import get_logger

logger = get_logger(__name__)
db = DatabaseConnector(
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@localhost/{settings.POSTGRES_DB}"
)


def main():
    db.enable_postgis()
    db.create_all_tables()

    geojson_path = Path(__file__).parent.parent / "resources/geojson" / "UKR-ADM1_simplified.geojson"
    analyzer = GeoAnalyzer(geojson_path)

    if not db.get_features_geojson()["features"]:
        features = analyzer.get_features()
        for feature in features:
            db.create_feature(feature[0], feature[1])


if __name__ == "__main__":
    try:
        main()

    except Exception as e:
        logger.error(e)

    finally:
        db.drop_all_tables()
