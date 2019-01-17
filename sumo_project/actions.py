"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""

from typing import Iterable

import traci
from model import Area, Vehicle

"""
This module defines all possible actions on the simulation
"""

def compute_edge_weight(edge_id):
    """
    Sum the different pollutant emissions on the edge with the identifier edge_id
    :param edge_id: The edge ID
    :return: The sum (in mg) of all pollutant emissions
    """
    co2 = traci.edge.getCO2Emission(edge_id)
    co = traci.edge.getCOEmission(edge_id)
    nox = traci.edge.getNOxEmission(edge_id)
    hc = traci.edge.getHCEmission(edge_id)
    pmx = traci.edge.getPMxEmission(edge_id)

    return co2 + co + nox + hc + pmx


def adjust_edges_weights(area):
    """
    Changes the edge weight of all edges into the area
    :param area: The Area object
    :return:
    """
    area.weight_adjusted = True
    for lane in area._lanes:
        edge_id = traci.lane.getEdgeID(lane.lane_id)
        weight = compute_edge_weight(edge_id)  # by default edges weight = length/mean speed
        traci.edge.setEffort(edge_id, weight)

    for veh_id in traci.vehicle.getIDList():
        traci.vehicle.rerouteEffort(veh_id)


def limit_speed_into_area(area: Area, speed_rf):
    """
    Limit the speed into the area by speed_rf factor
    :param area: The Area object
    :param speed_rf: The speed reduction factor (must be positive)
    :return:
    """
    area.limited_speed = True
    for lane in area._lanes:
        traci.lane.setMaxSpeed(lane.lane_id, speed_rf * lane.initial_max_speed)


def modifyLogic(logic, rf):
    """
    Change the logic of a traffic light by decreasing the overall duration of the traffic light
    :param logic: The Logic object
    :param rf: The reduction factor (must be positive)
    :return: A new Logic object with all phases modified
    """
    new_phases = []
    for phase in logic._phases:
        new_phase = traci.trafficlight.Phase(phase.duration * rf, phase.minDuration * rf, phase.maxDuration * rf,
                                             phase.phaseDef)
        new_phases.append(new_phase)

    return traci.trafficlight.Logic("new-program", 0, 0, 0, new_phases)


def adjust_traffic_light_phase_duration(area, reduction_factor):
    """
    Set all logics modification on traffic lights into the area
    :param area: The Area object
    :param reduction_factor: The reduction factor (must be positive)
    :return:
    """
    area.tls_adjusted = True
    for tl in area._tls:
        for logic in tl._logics:
            traci.trafficlights.setCompleteRedYellowGreenDefinition(tl.tl_id, modifyLogic(logic, reduction_factor))


def count_vehicles_in_area(area):
    """
    Count the vehicles number into the area
    :param area: The Area object
    :return: The number of vehicles into the area
    """
    vehicles_in_area = 0
    for lane in area._lanes:
        vehicles_in_area += traci.lane.getLastStepVehicleNumber(lane.lane_id)
    return vehicles_in_area


def lock_area(area):
    """
    Prohibits access to the area to a particular vehicle class
    NOT FIXED : Some vehicles continue to go into the area if they can not turn around and stay there
    :param area: The Area object
    :return:
    """
    area.locked = True
    for lane in area._lanes:
        # The passenger class is an example, you have to adapt this code
        traci.lane.setDisallowed(lane.lane_id, 'passenger')


def reverse_actions(area):
    """
    Reverse all actions made in an area
    :param area: The Area object
    :return:
    """
    # Reset max speed to original
    if area.limited_speed:
        area.limited_speed = False
        for lane in area._lanes:
            traci.lane.setMaxSpeed(lane.lane_id, lane.initial_max_speed)

    # Reset traffic lights initial duration
    if area.tls_adjusted:
        area.tls_adjusted = False
        for tl in area._tls:
            for initial_logic in tl._logics:
                traci.trafficlights.setCompleteRedYellowGreenDefinition(tl.tl_id, initial_logic._logic)

    # Unlock the area
    if area.locked:
        area.locked = False
        for lane in area._lanes:
            traci.lane.setAllowed(lane.lane_id, '')  # empty means all classes are allowed
