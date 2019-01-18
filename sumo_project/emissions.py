"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""

import argparse
import csv
import datetime
import itertools
import os
import sys
import time
from typing import List

import actions
import traci
from config import Config
from model import Area, Vehicle, Lane, TrafficLight, Phase, Logic, Emission
from parse import search
from shapely.geometry import LineString

"""
This module defines the entry point of the application 
"""


def init_grid(simulation_bounds, areas_number, window_size):
    """
    Initialize the grid of the loaded map from the configuration
    :param simulation_bounds: The map bounds
    :param areas_number: The number of areas
    :param window_size: The size of the acquisition window
    :return: A list of areas
    """
    grid = list()
    width = simulation_bounds[1][0] / areas_number
    height = simulation_bounds[1][1] / areas_number
    for i in range(areas_number):
        for j in range(areas_number):
            # bounds coordinates for the area : (xmin, ymin, xmax, ymax)
            ar_bounds = ((i * width, j * height), (i * width, (j + 1) * height),
                         ((i + 1) * width, (j + 1) * height), ((i + 1) * width, j * height))
            name = 'Area ({},{})'.format(i, j)
            area = Area(ar_bounds, name, window_size)
            grid.append(area)
            traci.polygon.add(area.name, ar_bounds, (255, 0, 0))  # Add polygon for UI
    return grid


def get_all_lanes() -> List[Lane]:
    """
    Recover and creates a list of Lane objects
    :return: The lanes list
    """
    lanes = []
    for lane_id in traci.lane.getIDList():
        polygon_lane = LineString(traci.lane.getShape(lane_id))
        initial_max_speed = traci.lane.getMaxSpeed(lane_id)
        lanes.append(Lane(lane_id, polygon_lane, initial_max_speed))
    return lanes


def parse_phase(phase_repr):
    """
    Because the SUMO object Phase does not contain accessors,
    we parse the string representation to retrieve data members.
    :param phase_repr: The Phase string representation
    :return: An new Phase instance
    """
    duration = search('duration: {:f}', phase_repr)
    min_duration = search('minDuration: {:f}', phase_repr)
    max_duration = search('maxDuration: {:f}', phase_repr)
    phase_def = search('phaseDef: {}\n', phase_repr)

    if phase_def is None:
        phase_def = ''
    else:
        phase_def = phase_def[0]

    return Phase(duration[0], min_duration[0], max_duration[0], phase_def)


def add_data_to_areas(areas: List[Area]):
    """
    Adds all recovered data to different areas
    :param areas: The list of areas
    :return:
    """
    lanes = get_all_lanes()
    for area in areas:
        for lane in lanes:  # add lanes 
            if area.rectangle.intersects(lane.polygon):
                area.add_lane(lane)
                for tl_id in traci.trafficlight.getIDList():  # add traffic lights 
                    if lane.lane_id in traci.trafficlight.getControlledLanes(tl_id):
                        logics = []
                        for l in traci.trafficlight.getCompleteRedYellowGreenDefinition(tl_id):  # add logics 
                            phases = []
                            for phase in traci.trafficlight.Logic.getPhases(l):  # add phases to logics
                                phases.append(parse_phase(phase.__repr__()))
                            logics.append(Logic(l, phases))
                        area.add_tl(TrafficLight(tl_id, logics))


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
    csv_dir = 'csv'
    if not os.path.exists(csv_dir):
        os.mkdir(csv_dir)

    now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    with open(f'csv/{now}.csv', 'w') as f:
        writer = csv.writer(f)
        # Write CSV headers
        writer.writerow(itertools.chain(('Step',), (a.name for a in grid)))
        # Write all areas emission value for each step
        for step in range(config.n_steps):
            em_for_step = (f'{a.emissions_by_step[step].value():.3f}' for a in grid)
            writer.writerow(itertools.chain((step,), em_for_step))


def run(config, logger, csv_export):
    """
    Run the simulation with the configuration chosen
    :param config: The simulation configuration
    :param logger: The simulation logger
    :return:
    """
    grid = list()
    try:
        traci.start(config.sumo_cmd)
        logger.info(f'Loaded simulation file : {config._SUMOCFG}')
        logger.info('Loading data for the simulation')
        start = time.perf_counter()

        grid = init_grid(traci.simulation.getNetBoundary(), config.areas_number, config.window_size)
        add_data_to_areas(grid)

        loading_time = round(time.perf_counter() - start, 2)
        logger.info(f'Data loaded ({loading_time}s)')

        logger.info('Simulation started...')
        step = 0
        while step < config.n_steps:
            traci.simulationStep()

            vehicles = get_all_vehicles()
            get_emissions(grid, vehicles, step, config, logger)
            step += 1

            print(f'step = {step}/{config.n_steps}', end='\r')

    finally:
        traci.close(False)

        if csv_export:
            export_data_to_csv(config, grid)
            logger.info(f'Exported data into the csv folder')

        simulation_time = round(time.perf_counter() - start, 2)
        logger.info(f'End of the simulation ({simulation_time}s)')

        # 1 step is equal to one second simulated
        logger.info(f'Real-time factor : {config.n_steps / simulation_time}')

        total_emissions = Emission()
        for area in grid:
            total_emissions += area.sum_all_emissions()

        logger.info(f'Total emissions = {total_emissions.value()} mg')

        if not config.without_actions_mode:  # If it's not a simulation without actions
            ref = config.get_ref_emissions()
            if not (ref is None):  # If a reference value exist (add yours into config.py)
                global_diff = (ref.value() - total_emissions.value()) / ref.value()

                logger.info(f'Global reduction percentage of emissions = {global_diff * 100} %')
                logger.info(f'-> CO2 emissions = {get_reduction_percentage(ref.co2, total_emissions.co2)} %')
                logger.info(f'-> CO emissions = {get_reduction_percentage(ref.co, total_emissions.co)} %')
                logger.info(f'-> Nox emissions = {get_reduction_percentage(ref.nox, total_emissions.nox)} %')
                logger.info(f'-> HC emissions = {get_reduction_percentage(ref.hc, total_emissions.hc)} %')
                logger.info(f'-> PMx emissions = {get_reduction_percentage(ref.pmx, total_emissions.pmx)} %')


def add_options(parser):
    """
    Add command line options
    :param parser: The command line parser
    :return:
    """
    parser.add_argument("-f", "--configfile", type=str, default='configs/default_config.json', required=False,
                        help='Choose your configuration file from your working directory')
    parser.add_argument("-save", "--save", action="store_true",
                        help='Save the logs into the logs folder')
    parser.add_argument("-steps", "--steps", type=int, default=200, required=False,
                        help='Choose the simulated time (in seconds)')
    parser.add_argument("-ref", "--ref", action="store_true",
                        help='Launch a reference simulation (without acting on areas)')
    parser.add_argument("-gui", "--gui", action="store_true",
                        help="Show UI")
    parser.add_argument("-csv", "--csv", action="store_true",
                        help="Export all data emissions into a CSV file")


def main(args):
    """
    The entry point of the application
    :param args: Command line options
    :return:
    """
    parser = argparse.ArgumentParser(description="")
    add_options(parser)
    args = parser.parse_args(args)

    config = Config()
    config.import_config_file(args.configfile)  # By default the configfile is default_config.json
    config.init_traci()
    logger = config.init_logger(save_logs=args.save)
    csv_export = False

    if args.ref:
        config.without_actions_mode = True
        logger.info(f'Reference simulation')

    if args.steps:
        config.n_steps = args.steps

    if args.gui:
        config._SUMOCMD = "sumo-gui"

    if args.csv:
        csv_export = True

    config.check_config()

    logger.info(f'Loaded configuration file : {args.configfile}')
    logger.info(f'Simulated time : {args.steps}s')
    run(config, logger, csv_export)


if __name__ == '__main__':
    main(sys.argv[1:])
