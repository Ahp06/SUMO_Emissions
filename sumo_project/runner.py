'''
Created on 19 janv. 2019

@author: Admin
'''

import argparse
import os
import sys
import time
import traci

import jsonpickle

from config import Config
from data import Data
import emissions
from model import Emission


def add_options(parser):
    """
    Add command line options
    :param parser: The command line parser
    :return:
    """
    parser.add_argument("-new_dump", "--new_dump", metavar=('config_file', 'dump_name'), nargs=2, type=str,
                        required=False, help='Load and create a new data dump with the configuration file chosen')
    parser.add_argument("-run", "--run", type=str, required=False,
                        help='Run a simulation with the dump chosen')
        
    parser.add_argument("-save", "--save", action="store_true",
                        help='Save the logs into the logs folder')
    parser.add_argument("-csv", "--csv", action="store_true",
                        help="Export all data emissions into a CSV file")


def create_dump(config_file, dump_name):
    
    config = Config()
    config.import_config_file(config_file)
    config.check_config()
    config.init_traci()
    
    sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo')
    sumo_cmd = [sumo_binary, "-c", config._SUMOCFG]
    
    traci.start(sumo_cmd)
    if not os.path.isfile(f'files/dump/{dump_name}.json'):
        start = time.perf_counter()
        data = Data(traci.simulation.getNetBoundary(), config)
        data.init_grid()
        data.add_data_to_areas() 
        data.save(dump_name)
        
        loading_time = round(time.perf_counter() - start, 2)
        print(f'Data loaded ({loading_time}s)')
        print(f'Dump {dump_name} created')
    else:
        print(f'Dump with name {dump_name} already exist') 
        
    traci.close(False)


def run(data : Data, config : Config, logger):
    try:
        traci.start(config.sumo_cmd)
                        
        for area in data.grid: 
            traci.polygon.add(area.name, area.rectangle.exterior.coords, (255, 0, 0))  # Add polygon for UI

        logger.info(f'Loaded simulation file : {config._SUMOCFG}')
        logger.info('Loading data for the simulation')
        start = time.perf_counter()
        
        logger.info('Simulation started...')
        step = 0
        while step < config.n_steps:
            traci.simulationStep()
    
            vehicles = emissions.get_all_vehicles()
            emissions.get_emissions(data.grid, vehicles, step, config, logger)
            step += 1
    
            print(f'step = {step}/{config.n_steps}', end='\r')
    
    finally:
        traci.close(False)
    
    
def main(args):
    """
    The entry point of the application
    :param args: Command line options
    :return:
    """
    parser = argparse.ArgumentParser()
    add_options(parser)
    args = parser.parse_args(args)
    
    if args.new_dump is not None:
        create_dump(args.new_dump[0], args.new_dump[1])
    
    if args.run is not None:
        dump_path = f'files/dump/{args.run}.json'
        if os.path.isfile(dump_path):
            with open(dump_path, 'r') as f:
                data = jsonpickle.decode(f.read())
            config = data.config
            logger = config.init_logger(save_logs=args.save)
            logger.info(f'Running simulation dump {args.run}...')  
            start = time.perf_counter()
            run(data, config, logger)

    if args.csv:
        emissions.export_data_to_csv(config, data.grid)
        logger.info(f'Exported data into the csv folder')
    
    simulation_time = round(time.perf_counter() - start, 2)
    logger.info(f'End of the simulation ({simulation_time}s)')
    
    # 1 step is equal to one second simulated
    logger.info(f'Real-time factor : {config.n_steps / simulation_time}')
    
    total_emissions = Emission()
    for area in data.grid:
        total_emissions += area.sum_all_emissions()
    
    logger.info(f'Total emissions = {total_emissions.value()} mg')
    
    if not config.without_actions_mode:  # If it's not a simulation without actions
        ref = config.get_ref_emissions()
        if not (ref is None):  # If a reference value exist (add yours into config.py)
            global_diff = (ref.value() - total_emissions.value()) / ref.value()
    
            logger.info(f'Global reduction percentage of emissions = {global_diff * 100} %')
            logger.info(f'-> CO2 emissions = {emissions.get_reduction_percentage(ref.co2, total_emissions.co2)} %')
            logger.info(f'-> CO emissions = {emissions.get_reduction_percentage(ref.co, total_emissions.co)} %')
            logger.info(f'-> Nox emissions = {emissions.get_reduction_percentage(ref.nox, total_emissions.nox)} %')
            logger.info(f'-> HC emissions = {emissions.get_reduction_percentage(ref.hc, total_emissions.hc)} %')
            logger.info(f'-> PMx emissions = {emissions.get_reduction_percentage(ref.pmx, total_emissions.pmx)} %')    

    
if __name__ == '__main__':
    main(sys.argv[1:])
