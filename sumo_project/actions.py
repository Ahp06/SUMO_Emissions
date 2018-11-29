"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""
from typing import Iterable

import traci
import inspect
from shapely.geometry.linestring import LineString

from model import Area, Vehicle
from traci._trafficlight import Logic, Phase


def remove_vehicle(veh_id):
    traci.vehicle.remove(veh_id, traci.constants.REMOVE_PARKING)

def compute_edge_weight(edge_id):
    return (traci.edge.getCOEmission(edge_id)
            + traci.edge.getNOxEmission(edge_id)
            + traci.edge.getHCEmission(edge_id)
            + traci.edge.getPMxEmission(edge_id)
            + traci.edge.getCO2Emission(edge_id))

def adjust_edges_weights():
    for edge_id in traci.edge.getIDList():
        weight = compute_edge_weight(edge_id)  # by default edges weight = length/mean speed
        traci.edge.adaptTraveltime(edge_id, weight)

def limit_speed_into_area(area: Area, vehicles: Iterable[Vehicle], max_speed):
    print(f'Setting max speed into {area.name} to {max_speed} km/h')
    area.locked = True
    for lane in area._lanes:
        traci.lane.setMaxSpeed(lane.lane_id, max_speed/3.6)


        
def adjust_traffic_light_phase_duration(area,reduction_factor):
    #attributes = inspect.getmembers(Phase, lambda a:not(inspect.isroutine(a))) 
    #print ([a[0] for a in attributes])
    for tl in area._tls:
        for logic in tl._logics:
           phases = traci.trafficlight.Logic.getPhases(logic)
           for phase in phases:
               print(phase)
    
    #phaseDuration = traci.trafficlight.getPhaseDuration(tl.tl_id)
    #traci.trafficlight.setPhaseDuration(tl.tl_id, phaseDuration*reduction_factor)