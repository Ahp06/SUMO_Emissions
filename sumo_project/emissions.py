import argparse
import csv
import datetime
import itertools
import os
import sys
import time
from typing import List

import traci
from parse import search
from shapely.geometry import LineString

import actions
from config import Config
from model import Area, Vehicle, Lane, TrafficLight, Phase, Logic, Emission

# Absolute path of the directory the script is in
SCRIPTDIR = os.path.dirname(__file__)


def init_grid(simulation_bounds, areas_number, window_size):
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
            traci.polygon.add(area.name, ar_bounds, (255, 0, 0))
    return grid


def get_all_lanes() -> List[Lane]:
    lanes = []
    for lane_id in traci.lane.getIDList():
        polygon_lane = LineString(traci.lane.getShape(lane_id))
        initial_max_speed = traci.lane.getMaxSpeed(lane_id)
        lanes.append(Lane(lane_id, polygon_lane, initial_max_speed))
    return lanes


def parse_phase(phase_repr):
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
    co2 = traci.vehicle.getCO2Emission(veh_id)
    co = traci.vehicle.getCOEmission(veh_id)
    nox = traci.vehicle.getNOxEmission(veh_id)
    hc = traci.vehicle.getHCEmission(veh_id)
    pmx = traci.vehicle.getPMxEmission(veh_id)

    return Emission(co2, co, nox, hc, pmx)


def get_all_vehicles() -> List[Vehicle]:
    vehicles = list()
    for veh_id in traci.vehicle.getIDList():
        veh_pos = traci.vehicle.getPosition(veh_id)
        vehicle = Vehicle(veh_id, veh_pos)
        vehicle.emissions = compute_vehicle_emissions(veh_id)
        vehicles.append(vehicle)
    return vehicles


def get_emissions(grid: List[Area], vehicles: List[Vehicle], current_step, config, logger):
    for area in grid:
        total_emissions = Emission()
        for vehicle in vehicles:
            if vehicle.pos in area:
                total_emissions += vehicle.emissions

        area.emissions_by_step.append(total_emissions)

        if area.sum_emissions_into_window(current_step, config.window_size) >= config.emissions_threshold:

            if config.limit_speed_mode and not area.limited_speed:
                logger.info(f'Action - Decreased max speed into {area.name} by {config.speed_rf * 100}%')
                actions.limit_speed_into_area(area, vehicles, config.speed_rf)
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
    return (ref - total) / ref * 100


def export_data_to_csv(config, grid):
    csv_dir = os.path.join(SCRIPTDIR, 'csv')
    if not os.path.exists(csv_dir):
        os.mkdir(csv_dir)
    now = datetime.datetime.utcnow().isoformat()

    with open(os.path.join(csv_dir, f'{now}.csv'), 'w') as f:
        writer = csv.writer(f)
        # Write CSV headers
        writer.writerow(itertools.chain(('Step',), (a.name for a in grid)))
        # Write all areas emission value for each step
        for step in range(config.n_steps):
            em_for_step = (f'{a.emissions_by_step[step].value():.3f}' for a in grid)
            writer.writerow(itertools.chain((step,), em_for_step))


def run(config, logger):
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
        while step < config.n_steps:  # traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            vehicles = get_all_vehicles()
            get_emissions(grid, vehicles, step, config, logger)
            step += 1

            print(f'step = {step}/{config.n_steps}', end='\r')

    finally:
        traci.close(False)
        export_data_to_csv(config, grid)

        simulation_time = round(time.perf_counter() - start, 2)
        logger.info(f'End of the simulation ({simulation_time}s)')
        logger.info(f'Real-time factor : {config.n_steps / simulation_time}')

        total_emissions = Emission()
        for area in grid:
            total_emissions += area.sum_all_emissions()

        logger.info(f'Total emissions = {total_emissions.value()} mg')

        if not config.without_actions_mode:
            ref = config.get_ref_emissions()
            if not (ref is None):
                global_diff = (ref.value() - total_emissions.value()) / ref.value()

                logger.info(f'Global reduction percentage of emissions = {global_diff * 100} %')
                logger.info(f'-> CO2 emissions = {get_reduction_percentage(ref.co2, total_emissions.co2)} %')
                logger.info(f'-> CO emissions = {get_reduction_percentage(ref.co, total_emissions.co)} %')
                logger.info(f'-> Nox emissions = {get_reduction_percentage(ref.nox, total_emissions.nox)} %')
                logger.info(f'-> HC emissions = {get_reduction_percentage(ref.hc, total_emissions.hc)} %')
                logger.info(f'-> PMx emissions = {get_reduction_percentage(ref.pmx, total_emissions.pmx)} %')


def add_options(parser):
    parser.add_argument("-f", "--configfile", type=str, default='configs/default_config.json', required=False,
                        help='Choose your configuration file from your working directory')
    parser.add_argument("-save", "--save", action="store_true",
                        help='Save the logs into the logs folder')
    parser.add_argument("-steps", "--steps", type=int, default=200, required=False,
                        help='Choose the simulated time (in seconds)')
    parser.add_argument("-ref", "--ref", action="store_true",
                        help='Launch a reference simulation (without acting on areas)')
    parser.add_argument("-gui", "--gui", action="store_true",
                        help="Set GUI mode")


def main(args):
    parser = argparse.ArgumentParser(description="")
    add_options(parser)
    args = parser.parse_args(args)

    config = Config()
    config.import_config_file(args.configfile)
    config.init_traci()
    logger = config.init_logger(save_logs=args.save)

    if args.ref:
        config.without_actions_mode = True
        logger.info(f'Reference simulation')

    if args.steps:
        config.n_steps = args.steps

    if args.gui:
        config._SUMOCMD = "sumo-gui"

    config.check_config()

    logger.info(f'Loaded configuration file : {args.configfile}')
    logger.info(f'Simulated time : {args.steps}s')
    run(config, logger)


if __name__ == '__main__':
    main(sys.argv[1:])
