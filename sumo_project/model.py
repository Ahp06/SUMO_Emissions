"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""

"""
This module defines the business model of our application
"""

import collections
from traci._trafficlight import Logic as SUMO_Logic
from typing import Tuple, Set

from shapely.geometry import Point, LineString
from shapely.geometry import Polygon
from shapely.geometry.base import BaseGeometry


class Lane:
    """
    The Lane class includes the polygon defining the lane
    and keep in memory the initial maximum speed on the lane
    """

    def __init__(self, lane_id: str, polygon: LineString, initial_max_speed: float):
        """
        Lane constructor

        :param lane_id: The ID of the lane
        :param polygon: The polygon defining the shape of the lane
        :param initial_max_speed: The initial maximum speed
        """
        self.polygon = polygon
        self.lane_id = lane_id
        self.initial_max_speed = initial_max_speed

    def __hash__(self):
        """Overrides the default implementation"""
        return hash(self.lane_id)


class Phase:
    """
    The Phase class defines a phase of a traffic light
    """

    def __init__(self, duration: float, minDuration: float, maxDuration: float, phaseDef: str):
        """
        Phase constructor

        :param duration: The duration of the phase (in seconds)
        :param minDuration: The minimum duration of the phase
        :param maxDuration: The maximum duration of the phase
        :param phaseDef: The definition of the phase, following the definition rules of SUMO
        (See : http://sumo.dlr.de/wiki/Simulation/Traffic_Lights#.3Cphase.3E_Attributes)
        """

        self.duration = duration
        self.minDuration = minDuration
        self.maxDuration = maxDuration
        self.phaseDef = phaseDef

    def __repr__(self) -> str:
        """
        :return: The Phase string representation
        """
        repr = f'Phase(duration:{self.duration},minDuration:{self.minDuration},maxDuration:{self.maxDuration},phaseDef:{self.phaseDef})'
        return str(repr)


class Logic:
    """
    The Logic class defines the strategy of a traffic light.
    This class includes the Logic instance of SUMO with all phases corresponding to it.
    A Logic object contains multiple phases.
    """

    def __init__(self, logic: SUMO_Logic, phases: Set[Phase]):
        """
        Logic constructor
        :param logic: The SUMO Logic object
        :param phases: The list of phases belonging to this logic
        """
        self._logic = logic
        self._phases: Set[Phase] = phases


class TrafficLight:
    """
    This TrafficLight class defines a traffic light
    """

    def __init__(self, tl_id: str, logics: Set[Logic]):
        """
        TrafficLight constructor
        :param tl_id: The traffic light ID
        :param logics: The list of logics belonging to the traffic light
        """
        self.tl_id = tl_id
        self._logics: Set[Logic] = logics

    def __hash__(self):
        """Overrides the default implementation"""
        return hash(self.tl_id)


class Emission:
    """
    This class defines the different pollutant emissions
    """

    def __init__(self, co2=0, co=0, nox=0, hc=0, pmx=0):
        """
        Emission constructor
        :param co2: Quantity of CO2(in mg)
        :param co: Quantity of C0(in mg)
        :param nox: Quantity of Nox(in mg)
        :param hc: Quantity of HC(in mg)
        :param pmx: Quantity of PMx(in mg)
        """
        self.co2 = co2
        self.co = co
        self.nox = nox
        self.hc = hc
        self.pmx = pmx

    def __add__(self, other):
        """
        Add two emission objects
        :param other: The other Emission object to add
        :return: A new object whose emission values ​​are the sum of both Emission object
        """
        return Emission(self.co2 + other.co2, self.co + other.co, self.nox + other.nox, self.hc + other.hc,
                        self.pmx + other.pmx)

    def value(self):
        """
        :return: The sum of all emissions
        """
        return self.co2 + self.co + self.nox + self.hc + self.pmx

    def __repr__(self) -> str:
        """
        :return: The Emission string representation
        """
        repr = f'Emission(co2={self.co2},co={self.co},nox={self.nox},hc={self.hc},pmx={self.pmx})'
        return str(repr)


class Area:
    """
    The Area class defines a grid area of the simulation map
    """

    def __init__(self, coords, name):
        """
        Area constructor
        :param coords: The coordinates of the zone,
        defined by the bounds coordinates of this area : (xmin, ymin, xmax, ymax)
        :param name: The Area name
        """
        self.limited_speed = False
        self.locked = False
        self.tls_adjusted = False
        self.weight_adjusted = False
        self.rectangle = Polygon(coords)
        self.name = name
        self.emissions_by_step = []
        self._lanes: Set[Lane] = set()
        self._tls: Set[TrafficLight] = set()

    def set_window_size(self, window_size):
        self.window = collections.deque(maxlen=window_size)
        
    def __eq__(self, other):
        """
        Overrides the equal definition
        :param other: The other Area object
        :return: True if the two rectangles are equals
        """
        return self.rectangle.__eq__(other)

    def __contains__(self, item):
        """
        :param item: A position on the map
        :return: True if the area contains the item
        """
        return self.rectangle.contains(item)

    @property
    def bounds(self):
        """
        Return the bounds rectangle of this area
        :return:
        """
        return self.rectangle.bounds

    def intersects(self, other: BaseGeometry) -> bool:
        """
        :param other: A BaseGeometry object
        :return: True if this area intersects with other
        """
        return self.rectangle.intersects(other)

    def add_lane(self, lane: Lane):
        """
        Add a new lane object into lanes list
        :param lane: A Lane object
        :return:
        """
        self._lanes.add(lane)

    def add_tl(self, tl: TrafficLight):
        """
        Add a new trafficLight object into lanes list
        :param tl: A TrafficLight object
        :return:
        """
        self._tls.add(tl)

    def remove_lane(self, lane: Lane):
        """
        Remove a lane from lanes list
        :param lane: The Lane object to remove
        :return:
        """
        self._lanes.remove(lane)

    def sum_all_emissions(self):
        """
        Sum all Emissions object from initial step to final step
        :return: The sum Emission object
        """
        sum = Emission()
        for emission in self.emissions_by_step:
            sum += emission
        return sum

    def sum_emissions_into_window(self, current_step):
        """
        Sum all Emissions object into the acquisition window
        :param current_step: The current step of the simulation
        :return:
        """
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
    """
    The Vehicle class defines a vehicle object
    """

    def __init__(self, veh_id: int, pos: Tuple[float, float]):
        """
        Vehicle constructor
        :param veh_id: The vehicle ID
        :param pos: The position of the vehicle one the map
        """
        self.emissions: Emission = Emission()
        self.veh_id = veh_id
        self.pos = Point(pos)

    def __repr__(self) -> str:
        """
        :return: The Vehicle string representation
        """
        return str(self.__dict__)
