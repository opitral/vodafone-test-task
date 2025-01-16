from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
from shapely import Point, Polygon, MultiPolygon
from sqlalchemy import String, Integer, Column, ForeignKey, Float, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Direction(Enum):
    NORTH = "north"
    SOUTH = "south"
    WEST = "west"
    EAST = "east"


@dataclass
class ExtremePoint:
    direction: Direction
    point: Point


class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    multi_polygon = Column(Geometry("MultiPolygon", srid=4326), nullable=False)

    def __repr__(self):
        return f"Feature<id={self.id}, name={self.name}>"

    @property
    def shapely_multi_polygon(self) -> MultiPolygon:
        return to_shape(self.multi_polygon)


class Grid(Base):
    __tablename__ = "grids"

    id = Column(Integer, primary_key=True, autoincrement=True)
    size = Column(Float, nullable=False)

    squares = relationship("Square", back_populates="grid")

    @property
    def matches(self) -> List["Square"]:
        return [square for square in self.squares if square.is_matching]

    @property
    def not_matches(self) -> List["Square"]:
        return [square for square in self.squares if not square.is_matching]

    def __repr__(self):
        return f"Grid<id={self.id}, size={self.size}>"


class Square(Base):
    __tablename__ = "squares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    grid_id = Column(Integer, ForeignKey("grids.id"), nullable=False)
    is_matching = Column(Boolean, nullable=False, default=True)

    grid = relationship("Grid", back_populates="squares")
    vertices = relationship("Vertex", back_populates="square")

    @property
    def shapely_polygon(self) -> Polygon:
        points = [vertex.shapely_point for vertex in self.vertices]

        if len(points) >= 3 and points[0] != points[-1]:
            points.append(points[0])

        return Polygon(points)

    @property
    def size(self) -> int | None:
        if not self.vertices or len(self.vertices) < 3:
            return None

        polygon = self.shapely_polygon
        minx, miny, maxx, maxy = polygon.bounds
        return round((maxx - minx) * 111, 2)

    def __repr__(self):
        return f"Square<id={self.id}, size={self.size if self.size else 'Unknown'}>"


class Vertex(Base):
    __tablename__ = "vertices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    point = Column(Geometry("Point", srid=4326), nullable=False)
    square_id = Column(Integer, ForeignKey("squares.id"), nullable=False)

    square = relationship("Square", back_populates="vertices")
    sectors = relationship("Sector", back_populates="vertex")
    sector_intersections = relationship("SectorVertexIntersection", back_populates="vertex")

    @property
    def shapely_point(self) -> Point:
        return to_shape(self.point)

    def __repr__(self):
        return f"Vertex<id={self.id}, square_id={self.square_id}>"


class Sector(Base):
    __tablename__ = "sectors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vertex_id = Column(Integer, ForeignKey("vertices.id"), nullable=False)
    azimuth = Column(Integer, nullable=False)
    radius = Column(Integer, nullable=False)
    angle = Column(Integer, nullable=False)
    polygon = Column(Geometry("Polygon", srid=4326), nullable=False)

    vertex = relationship("Vertex", back_populates="sectors")
    vertex_intersections = relationship("SectorVertexIntersection", back_populates="sector")

    def __repr__(self):
        return f"Sector<azimuth={self.azimuth}, radius={self.radius}, angle={self.angle}>"

    @property
    def shapely_polygon(self) -> Polygon:
        return to_shape(self.polygon)

    def check_vertex_intersection(self, vertex: Vertex) -> bool:
        return vertex.shapely_point.within(self.shapely_polygon)

    def check_square_vertices_intersection(self, square: Square) -> Tuple[bool, Vertex]:
        for vertex in square.vertices:
            yield self.check_vertex_intersection(vertex), vertex


class SectorVertexIntersection(Base):
    __tablename__ = "sector_vertex_intersections"

    sector_id = Column(Integer, ForeignKey("sectors.id"), primary_key=True)
    vertex_id = Column(Integer, ForeignKey("vertices.id"), primary_key=True)

    sector = relationship("Sector", back_populates="vertex_intersections")
    vertex = relationship("Vertex", back_populates="sector_intersections")

    def __repr__(self):
        return f"SectorVertexIntersection<sector_id={self.sector_id}, vertex_id={self.vertex_id}>"
