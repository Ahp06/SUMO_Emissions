"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""
from typing import Iterable

import traci
from shapely.geometry.linestring import LineString

from model import Area, Vehicle
from traci._trafficlight import Logic

def remove_vehicles(vehicles):
    print(f'Removed {vehicles.size} vehicles from the simulation')
    for vehicle in vehicles:
        traci.vehicle.remove(vehicle.veh_id, traci.constants.REMOVE_PARKING)

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

def modifyLogic(logic, rf): #rf for "reduction factor" 
    new_phases = [] 
    for phase in logic._phases:
        new_phase = traci.trafficlight.Phase(phase.duration*rf,phase.minDuration*rf,phase.maxDuration*rf,phase.phaseDef)
        new_phases.append(new_phase)
        
    return traci.trafficlight.Logic("new-program", 0 , 0 , 0 , new_phases)    

def adjust_traffic_light_phase_duration(area, reduction_factor):
    print(f'Decrease of traffic lights duration by a factor of {reduction_factor}')
    for tl in area._tls:
        for logic in tl._logics:
            traci.trafficlights.setCompleteRedYellowGreenDefinition(tl.tl_id, modifyLogic(logic,reduction_factor))
    
    #phaseDuration = traci.trafficlight.getPhaseDuration(tl.tl_id)
    #traci.trafficlight.setPhaseDuration(tl.tl_id, phaseDuration*reduction_factor)