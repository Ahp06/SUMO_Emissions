from shapely.geometry import Polygon
from shapely.geometry import Point


class Area:

    def __init__(self, coords, name=''):
        self.rectangle = Polygon(coords)
        self.name = name
        self.emissions = 0.0

    def __eq__(self, other):
        return self.rectangle.__eq__(other)

    @property
    def bounds(self):
        return self.rectangle.bounds

    def contains(self, other):
        return self.rectangle.contains(Point(other))

    @classmethod
    def from_bounds(cls, xmin, ymin, xmax, ymax):
        return cls((
            (xmin, ymin),
            (xmin, ymax),
            (xmax, ymax),
            (xmax, ymin)))
