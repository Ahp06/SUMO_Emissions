"""
This module defines how pollutant emissions are recovered and how we act on the areas 
"""

import traci
from typing import List

import actions
from model import  Vehicle, Emission
from runner import RunProcess


def compute_vehicle_emissions(veh_id):
    """
    Recover the emissions of different pollutants from a vehicle and create an Emission instance
    :param veh_id: The vehicle ID
    :return: A new Emission instance
    """
    co2 = traci.vehicle.getCO2Emission(veh_id)
    co = traci.vehicle.getCOEmission(veh_id)
    nox = traci.vehicle.getNOxEmission(veh_id)
    hc = traci.vehicle.getHCEmission(veh_id)
    pmx = traci.vehicle.getPMxEmission(veh_id)

    return Emission(co2, co, nox, hc, pmx)


def get_all_vehicles() -> List[Vehicle]:
    """
    Recover all useful information about vehicles and creates a vehicles list
    :return: A list of vehicles instances
    """
    vehicles = list()
    for veh_id in traci.vehicle.getIDList():
        veh_pos = traci.vehicle.getPosition(veh_id)
        vehicle = Vehicle(veh_id, veh_pos)
        vehicle.emissions = compute_vehicle_emissions(veh_id)
        vehicles.append(vehicle)
    return vehicles

def get_emissions(p : RunProcess, vehicles: List[Vehicle], current_step):
    """
    For each area retrieves the acquired emissions in the window,
    and acts according to the configuration chosen by the user
    :param p: The current process
    :param vehicles: The list of vehicles
    :param current_step: The simulation current step
    :return:
    """
    for area in p.data.grid:
        total_emissions = Emission()
        for vehicle in vehicles:
            if vehicle.pos in area:
                total_emissions += vehicle.emissions

        # Adding of the total of emissions pollutant at the current step into memory
        area.emissions_by_step.append(total_emissions)
        
        # If the sum of pollutant emissions (in mg) exceeds the threshold
        if area.sum_emissions_into_window(current_step) >= p.config.emissions_threshold:

            if p.config.limit_speed_mode and not area.limited_speed:
                p.logger.info(f'Action - Decreased max speed into {area.name} by {p.config.speed_rf * 100}%')
                actions.limit_speed_into_area(area, p.config.speed_rf)
                if p.config.adjust_traffic_light_mode and not area.tls_adjusted:
                    p.logger.info(
                        f'Action - Decreased traffic lights duration by {p.config.trafficLights_duration_rf * 100}%')
                    actions.adjust_traffic_light_phase_duration(area, p.config.trafficLights_duration_rf)

            if p.config.lock_area_mode and not area.locked:
                if actions.count_vehicles_in_area(area):
                    p.logger.info(f'Action - {area.name} blocked')
                    actions.lock_area(area)

            if p.config.weight_routing_mode and not area.weight_adjusted:
                actions.adjust_edges_weights(area)

            traci.polygon.setFilled(area.name, True)

        else:
            if area.infrastructure_changed():
                p.logger.info(f'Action - Reversed actions into area {area.name}')
                actions.reverse_actions(area)
                traci.polygon.setFilled(area.name, False)


def get_reduction_percentage(ref, total):
    """
    Return the reduction percentage of total emissions between reference and an other simulation
    :param ref: The sum of all pollutant emissions (in mg) for the simulation of reference
    :param total: The sum of all pollutant emissions (in mg) for the current simulation launched
    :return:
    """
    return (ref - total) / ref * 100

