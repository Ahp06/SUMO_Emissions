from typing import Tuple, Set

from shapely.geometry import Point, LineString
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry


class Lane:

    def __init__(self, lane_id: str, polygon: LineString):
        self.polygon = polygon
        self.lane_id = lane_id

    def __hash__(self):
        """Overrides the default implementation"""
        return hash(self.lane_id)


class Area:

    def __init__(self, coords, name=''):
        self.locked = False
        self.rectangle = Polygon(coords)
        self.name = name
        self.emissions = 0.0
        self._lanes: Set[Lane] = set()

    def __eq__(self, other):
        return self.rectangle.__eq__(other)

    def __contains__(self, item):
        return self.rectangle.contains(item)

    @property
    def bounds(self):
        return self.rectangle.bounds

    def intersects(self, other: BaseGeometry) -> bool:
        return self.rectangle.intersects(other)

    def add_lane(self, lane: Lane):
        self._lanes.add(lane)

    def remove_lane(self, lane: Lane):
        self._lanes.remove(lane)

    @classmethod
    def from_bounds(cls, xmin, ymin, xmax, ymax):
        return cls((
            (xmin, ymin),
            (xmin, ymax),
            (xmax, ymax),
            (xmax, ymin)))


class Vehicle:

    def __init__(self, veh_id: int, pos: Tuple[float, float]):
        self.emissions: float = 0.0
        self.veh_id = veh_id
        self.pos = Point(pos)

    def __repr__(self) -> str:
        return str(self.__dict__)
