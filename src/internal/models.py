from sqlalchemy.orm import declarative_base
from sqlalchemy import String, Integer, Column
from geoalchemy2 import Geometry

Base = declarative_base()


class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    geom = Column(Geometry("MultiPolygon", srid=4326), nullable=False)

    def __repr__(self):
        return f"Feature(id={self.id}, name={self.name})"


class Square(Base):
    __tablename__ = "squares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    geom = Column(Geometry("Polygon", srid=4326), nullable=False)

    def __repr__(self):
        return f"Square(id={self.id})"
