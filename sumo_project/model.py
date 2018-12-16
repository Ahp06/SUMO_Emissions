import collections 
from traci._trafficlight import Logic as SUMO_Logic
from typing import Tuple, Set

from shapely.geometry import Point, LineString
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry


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

class Emission:
    def __init__(self, co2 = 0, co = 0 , nox = 0, hc = 0, pmx = 0):
        self.co2 = co2
        self.co = co
        self.nox = nox
        self.hc = hc
        self.pmx = pmx
    
    def __add__(self,other):
        return Emission(self.co2 + other.co2, self.co + other.co, self.nox + other.nox, self.hc + other.hc, self.pmx + other.pmx)
        
    
    def value(self):
        return self.co2 + self.co + self.nox + self.hc + self.pmx
    
    def __repr__(self) -> str:
        repr = f'Emission(co2={self.co2},co={self.co},nox={self.nox},hc={self.hc},pmx={self.pmx})'
        return str(repr)

class Area:

    def __init__(self, coords, name, window_size):
        self.limited_speed = False
        self.locked = False
        self.tls_adjusted = False
        self.weight_adjusted = False
        self.rectangle = Polygon(coords)
        self.name = name
        self.emissions_by_step = []
        self.window = collections.deque(maxlen = window_size)
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
        
    def sum_all_emissions(self):
        sum = Emission()
        for emission in self.emissions_by_step:
            sum += emission
        return sum 
    
    def sum_emissions_into_window(self, current_step, window_size): 

        self.window.appendleft(self.emissions_by_step[current_step].value())
        
        sum = 0
        for i in range(self.window.__len__()):
            sum += self.window[i]
        return sum

    @classmethod
    def from_bounds(cls, xmin, ymin, xmax, ymax):
        return cls((
            (xmin, ymin),
            (xmin, ymax),
            (xmax, ymax),
            (xmax, ymin)))

class Vehicle:

    def __init__(self, veh_id: int, pos: Tuple[float, float]):
        self.emissions: Emission = Emission()
        self.veh_id = veh_id
        self.pos = Point(pos)

    def __repr__(self) -> str:
        return str(self.__dict__)
