from typing import Tuple

from shapely.geometry import Point
from shapely.geometry import Polygon


class Area:

    def __init__(self, coords, name=''):
        self.rectangle = Polygon(coords)
        self.name = name
        self.emissions = 0.0

    def __eq__(self, other):
        return self.rectangle.__eq__(other)

    def __contains__(self, item):
        return self.rectangle.contains(item)

    @property
    def bounds(self):
        return self.rectangle.bounds

    @classmethod
    def from_bounds(cls, xmin, ymin, xmax, ymax):
        return cls((
            (xmin, ymin),
            (xmin, ymax),
            (xmax, ymax),
            (xmax, ymin)))


class Vehicle:

    def __init__(self, id: int, pos: Tuple[float, float]):
        self.id = id
        self.pos = Point(pos)

    def __repr__(self) -> str:
        return str(self.__dict__)
