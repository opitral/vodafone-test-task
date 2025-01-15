from typing import List

from shapely import Polygon
from shapely.geometry.base import BaseGeometry
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from geoalchemy2.shape import from_shape, to_shape

from internal.models import Base, Feature, Square
from internal.analyzer import Feature as FeatureModel
from pkg.logger import get_logger

logger = get_logger(__name__)


class DatabaseConnector:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self._initialize_database()

    def _initialize_database(self):
        Base.metadata.create_all(self.engine)
        logger.debug("All tables created")

    def drop_all_tables(self):
        Base.metadata.drop_all(self.engine)
        logger.debug("All tables dropped")

    def __del__(self):
        self.session.close()

    def create_feature(self, feature: FeatureModel):
        try:
            feature = Feature(
                name=feature.name,
                geom=from_shape(feature.geom, srid=4326)
            )
            self.session.add(feature)
            self.session.commit()
            logger.info(f"Feature '{feature.name}' created")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create feature '{feature.name}': {e}")

    def get_all_features(self) -> List[FeatureModel]:
        try:
            features = self.session.query(Feature).all()
            return [FeatureModel(name=str(f.name), geom=to_shape(f.geom)) for f in features]

        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch features: {e}")
            return []

    def delete_all_features(self):
        try:
            self.session.query(Feature).delete()
            self.session.commit()
            logger.info("All features deleted")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to delete features: {e}")

    def create_square(self, geom: BaseGeometry):
        try:
            square = Square(geom=from_shape(geom, srid=4326))
            self.session.add(square)
            self.session.commit()
            logger.info("Square created")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create square: {e}")

    def get_all_squares(self) -> List[Polygon]:
        try:
            squares = self.session.query(Square).all()
            return [to_shape(s.geom) for s in squares]
        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch squares: {e}")
            return []

    def delete_all_squares(self):
        try:
            self.session.query(Square).delete()
            self.session.commit()
            logger.info("All squares deleted")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to delete squares: {e}")
