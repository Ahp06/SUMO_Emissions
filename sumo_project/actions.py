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
            + traci.edge.getCO2Emission(edge_id))/(traci.edge.getLaneNumber(edge_id))

def adjust_edges_weights():     
    for edge_id in traci.edge.getIDList():
        weight = compute_edge_weight(edge_id)  # by default edges weight = length/mean speed
        traci.edge.setEffort(edge_id, weight)
        
    for veh_id in traci.vehicle.getIDList():
        traci.vehicle.rerouteEffort(veh_id)
        
def limit_speed_into_area(area: Area, vehicles: Iterable[Vehicle], speed_rf):
    area.limited_speed = True
    for lane in area._lanes:
        traci.lane.setMaxSpeed(lane.lane_id, speed_rf * lane.initial_max_speed)

def modifyLogic(logic, rf): #rf for "reduction factor" 
    new_phases = [] 
    for phase in logic._phases:
        new_phase = traci.trafficlight.Phase(phase.duration*rf,phase.minDuration*rf,phase.maxDuration*rf,phase.phaseDef)
        new_phases.append(new_phase)
        
    return traci.trafficlight.Logic("new-program", 0 , 0 , 0 , new_phases)    

def adjust_traffic_light_phase_duration(area, reduction_factor):
    area.tls_adjusted = True
    for tl in area._tls:
        for logic in tl._logics:
            traci.trafficlights.setCompleteRedYellowGreenDefinition(tl.tl_id, modifyLogic(logic,reduction_factor))
    
def count_vehicles_in_area(area):
    vehicles_in_area = 0 
    for lane in area._lanes:
        vehicles_in_area += traci.lane.getLastStepVehicleNumber(lane.lane_id)
    return vehicles_in_area

def lock_area(area):
    area.locked = True
    for lane in area._lanes:
        traci.lane.setDisallowed(lane.lane_id, 'passenger')