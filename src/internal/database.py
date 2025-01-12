import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from pkg.logger import get_logger


class DatabaseConnector:
    def __init__(self, connection_string: str):
        self.logger = get_logger(__name__)
        self.engine = create_engine(connection_string)
        self.session = sessionmaker(bind=self.engine)()

    def enable_postgis(self):
        self.session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        self.session.commit()
        self.logger.debug("PostGIS enabled")

    def create_all_tables(self):
        self.session.execute(text('''
            CREATE TABLE IF NOT EXISTS features (
                id   SERIAL PRIMARY KEY, 
                name VARCHAR(255)                     NULL, 
                geom GEOMETRY(MultiPolygon, 4326) NOT NULL
            )
        '''))
        self.session.commit()
        self.logger.debug("All tables created")

    def drop_all_tables(self):
        self.session.execute(text("DROP TABLE IF EXISTS features"))
        self.session.commit()
        self.logger.debug("All tables dropped")

    def __del__(self):
        self.session.close()
        self.logger.debug("Session closed")

    def create_feature(self, name: str, geom: dict):
        try:
            geojson_geom = json.dumps(geom)
            self.session.execute(text('''
                INSERT INTO features (name, geom) 
                VALUES (:name, ST_GeomFromGeoJSON(:geojson))
            '''), {"name": name, "geojson": geojson_geom})
            self.session.commit()
            self.logger.info(f"Feature {name} created")

        except Exception as e:
            self.logger.error(f"Failed to create feature {name}: {e}")

    def get_features_geojson(self):
        features = self.session.execute(text(
            "SELECT name, ST_AsGeoJSON(geom) AS geojson FROM features"
        )).fetchall()

        geojson = {
            "type": "FeatureCollection",
            "features": []
        }

        for name, geom in features:
            if geom:
                geojson["features"].append({
                    "type": "Feature",
                    "properties": {"name": name},
                    "geometry": json.loads(geom)
                })

        return geojson
