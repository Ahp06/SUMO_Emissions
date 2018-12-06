from typing import Tuple, Set

from shapely.geometry import Point, LineString
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry
from traci._trafficlight import Logic as SUMO_Logic


class Lane:

    def __init__(self, lane_id: str, polygon: LineString, initial_max_speed: float):
        self.polygon = polygon
        self.lane_id = lane_id
        self.initial_max_speed = initial_max_speed

    def __hash__(self):
        """Overrides the default implementation"""
        return hash(self.lane_id)

class Phase:
    def __init__(self, duration: float, minDuration: float, maxDuration : float, phaseDef: str):
        self.duration = duration 
        self.minDuration = minDuration
        self.maxDuration = maxDuration
        self.phaseDef = phaseDef 
        
    def __repr__(self) -> str:
        repr = f'Phase(duration:{self.duration},minDuration:{self.minDuration},maxDuration:{self.maxDuration},phaseDef:{self.phaseDef})'
        return str(repr)

class Logic:
    def __init__(self, logic: SUMO_Logic, phases: Set[Phase]):
        self._logic = logic
        self._phases: Set[Phase] = phases

class TrafficLight: 
    
    def __init__(self, tl_id: str, logics: Set[Logic]):
        self.tl_id = tl_id 
        self._logics: Set[Logic] = logics
        
    def __hash__(self):
        """Overrides the default implementation"""
        return hash(self.tl_id)
    
class Area:

    def __init__(self, coords, name=''):
        self.limited_speed = False
        self.locked = False
        self.rectangle = Polygon(coords)
        self.name = name
        self.emissions = 0.0
        self._lanes: Set[Lane] = set()
        self._tls: Set[TrafficLight] = set() 

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
        
    def add_tl(self, tl: TrafficLight):
        self._tls.add(tl)

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
