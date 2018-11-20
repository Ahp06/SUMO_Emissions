"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""
from typing import Iterable

import traci
from shapely.geometry.linestring import LineString

from model import Area, Vehicle


def remove_vehicle(veh_id):
    traci.vehicle.remove(veh_id, traci.constants.REMOVE_PARKING)

def lanes_in_area(area):
    for lane_id in traci.lane.getIDList():
        polygon_lane = LineString(traci.lane.getShape(lane_id))
        if area.rectangle.intersects(polygon_lane):
            yield lane_id

def computeEdgeWeight(edge_id):
    return (traci.edge.getCOEmission(edge_id)
    + traci.edge.getNOxEmission(edge_id)
    + traci.edge.getHCEmission(edge_id)
    + traci.edge.getPMxEmission(edge_id)
    + traci.edge.getCO2Emission(edge_id))
        
def adjustEdgesWeight():
    for edge_id in traci.edge.getIDList():
        weight = computeEdgeWeight(edge_id) #by default edges weight = length/mean speed
        traci.edge.adaptTraveltime(edge_id, weight) 

def lock_area(area: Area, vehicles: Iterable[Vehicle]):
    max_speed = 30
    print(f'Setting max speed into {area.name} to {max_speed} km/h')
    area.locked = True
    for lane in area._lanes:
        traci.lane.setMaxSpeed(lane.lane_id, max_speed/3.6)
    
