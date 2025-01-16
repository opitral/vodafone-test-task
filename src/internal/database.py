from geoalchemy2.shape import from_shape
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from internal.models import Base, Feature, Grid, Vertex, Square, Sector, SectorVertexIntersection
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

    def create_feature(self, model: Feature) -> int:
        try:
            model.geometry = from_shape(model.geometry, srid=4326)
            self.session.add(model)
            self.session.commit()
            logger.info(f"Feature '{model.name}' created")
            return model.id
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create feature '{model.name}': {e}")

    def get_all_features(self):
        try:
            return self.session.query(Feature).all()

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

    def create_square(self, model: Square) -> int:
        try:
            self.session.add(model)
            self.session.commit()
            logger.info("Square created")
            return model.id
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create square: {e}")

    def create_grid(self, model: Grid) -> int:
        try:
            self.session.add(model)
            self.session.commit()
            logger.info("Grid created")
            return model.id
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create grid: {e}")

    def create_vertex(self, model: Vertex) -> int:
        try:
            model.point = from_shape(model.point, srid=4326)
            self.session.add(model)
            self.session.commit()
            logger.info("Vertex created")
            return model.id
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create vertex: {e}")

    def create_sector(self, model: Sector) -> int:
        try:
            model.polygon = from_shape(model.polygon, srid=4326)
            self.session.add(model)
            self.session.commit()
            logger.info("Sector created")
            return model.id
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create sector: {e}")

    def get_all_sectors(self):
        try:
            return self.session.query(Sector).all()

        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch sectors: {e}")
            return []

    def get_all_squares(self):
        try:
            return self.session.query(Square).all()

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

    def delete_all_sectors(self):
        try:
            self.session.query(Sector).delete()
            self.session.commit()
            logger.info("All sectors deleted")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to delete sectors: {e}")

    def delete_all_vertices(self):
        try:
            self.session.query(Vertex).delete()
            self.session.commit()
            logger.info("All vertices deleted")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to delete vertices: {e}")

    def get_all_grids(self):
        try:
            return self.session.query(Grid).all()

        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch grids: {e}")
            return []

    def get_square_by_vertex_id(self, vertex_id: int):
        try:
            return self.session.query(Square).filter(Square.vertices.any(id=vertex_id)).first()

        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch square by vertex id: {e}")
            return None

    def get_grid_by_square_id(self, square_id: int):
        try:
            return self.session.query(Grid).filter_by(id=square_id).first()

        except SQLAlchemyError as e:
            logger.error(f"Failed to fetch grid by square id: {e}")
            return None

    def create_sector_vertex_intersection(self, model: SectorVertexIntersection):
        try:
            self.session.add(model)
            self.session.commit()
            logger.info("Sector-vertex intersection created")
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Failed to create sector-vertex intersection: {e}")
