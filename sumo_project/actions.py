"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""
from typing import Iterable

import traci
from shapely.geometry.linestring import LineString

from model import Area, Vehicle


def stop_vehicle(veh_id):
    traci.vehicle.remove(veh_id, traci.constants.REMOVE_PARKING)


def lanes_in_area(area):
    for lane_id in traci.lane.getIDList():
        polygon_lane = LineString(traci.lane.getShape(lane_id))
        if area.rectangle.intersects(polygon_lane):
            yield lane_id


def lock_area(area: Area, vehicles: Iterable[Vehicle]):
    for lane in area._lanes:
        print(f'Setting max speed of {lane.lane_id} to 30.')
        traci.lane.setMaxSpeed(lane.lane_id, 30)
    area.locked = True
    for vehicle in vehicles:
        traci.vehicle.rerouteTraveltime(vehicle.veh_id, True)
