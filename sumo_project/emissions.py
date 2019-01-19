"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""

"""
This module defines the entry point of the application 
"""

import argparse
import csv
import datetime
import itertools
import os
import sys
import time
import traci
from typing import List

import jsonpickle
from parse import search
from shapely.geometry import LineString

import actions
from config import Config
from data import Data
from model import Area, Vehicle, Lane, TrafficLight, Phase, Logic, Emission


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


def get_emissions(grid: List[Area], vehicles: List[Vehicle], current_step, config, logger):
    """
    For each area retrieves the acquired emissions in the window,
    and acts according to the configuration chosen by the user
    :param grid: The list of areas
    :param vehicles: The list of vehicles
    :param current_step: The simulation current step
    :param config: The simulation configuration
    :param logger: The simulation logger
    :return:
    """
    for area in grid:
        total_emissions = Emission()
        for vehicle in vehicles:
            if vehicle.pos in area:
                total_emissions += vehicle.emissions

        # Adding of the total of emissions pollutant at the current step into memory
        area.emissions_by_step.append(total_emissions)

        # If the sum of pollutant emissions (in mg) exceeds the threshold
        if area.sum_emissions_into_window(current_step) >= config.emissions_threshold:

            if config.limit_speed_mode and not area.limited_speed:
                logger.info(f'Action - Decreased max speed into {area.name} by {config.speed_rf * 100}%')
                actions.limit_speed_into_area(area, config.speed_rf)
                if config.adjust_traffic_light_mode and not area.tls_adjusted:
                    logger.info(
                        f'Action - Decreased traffic lights duration by {config.trafficLights_duration_rf * 100}%')
                    actions.adjust_traffic_light_phase_duration(area, config.trafficLights_duration_rf)

            if config.lock_area_mode and not area.locked:
                if actions.count_vehicles_in_area(area):
                    logger.info(f'Action - {area.name} blocked')
                    actions.lock_area(area)

            if config.weight_routing_mode and not area.weight_adjusted:
                actions.adjust_edges_weights(area)

            traci.polygon.setFilled(area.name, True)

        else:
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


def export_data_to_csv(config, grid):
    """
    Export all Emission objects as a CSV file into the csv directory
    :param config: The simulation configuration
    :param grid: The list of areas
    :return:
    """
    csv_dir = 'files/csv'
    if not os.path.exists(csv_dir):
        os.mkdir(csv_dir)

    now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    with open(f'files/csv/{now}.csv', 'w') as f:
        writer = csv.writer(f)
        # Write CSV headers
        writer.writerow(itertools.chain(('Step',), (a.name for a in grid)))
        # Write all areas emission value for each step
        for step in range(config.n_steps):
            em_for_step = (f'{a.emissions_by_step[step].value():.3f}' for a in grid)
            writer.writerow(itertools.chain((step,), em_for_step))

