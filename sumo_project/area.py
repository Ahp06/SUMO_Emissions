from shapely.geometry import Polygon
from shapely.geometry import Point


class Area:

    def __init__(self, coords, name=''):
        self.rectangle = Polygon(coords)
        self.name = name
        self.emissions = 0.0

    def __eq__(self, other):
        return self.rectangle.__eq__(other)

    def __contains__(self, item):
        return self.rectangle.contains(Point(item))

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
