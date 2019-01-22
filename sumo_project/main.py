'''
Created on 19 janv. 2019

@author: Axel Huynh-Phuc
'''

import sys
import os
import argparse
import traci
import time
import jsonpickle

from data import Data
from config import Config
from runner import RunProcess


"""
Init the Traci API
"""
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

        
def add_options(parser):
    """
    Add command line options
    :param parser: The command line parser
    :return:
    """
    
    # TODO: Faire que -areas & -simulation_dir soit requis si -new_dump 
    # Faire que -c soit requis si -run
     
    parser.add_argument("-new_dump", "--new_dump", type=str,
                        required=False, help='Load and create a new data dump with the configuration file chosen')
    parser.add_argument("-areas", "--areas", type=int, required=False,
                        help='Will create a grid with "areas x areas" areas')
    parser.add_argument("-simulation_dir", "--simulation_dir", type=str, required=False,
                        help='Choose the simulation directory')
    
    parser.add_argument("-run", "--run", type=str,
                        help='Run a simulation with the dump chosen')
    parser.add_argument("-c", "--c", nargs='+', type=str,
                        help='Choose your configuration file from your working directory')
    parser.add_argument("-save", "--save", action="store_true",
                        help='Save the logs into the logs folder')
    parser.add_argument("-csv", "--csv", action="store_true",
                        help="Export all data emissions into a CSV file")

    
def create_dump(dump_name, simulation_dir, areas_number):
    """
    Create a new dump with config file and dump_name chosen 
    :param dump_name: The name of the data dump
    :param simulation_dir: The simulation directory 
    :param areas_number: The number of areas in grid 
    :return:
    """
    
    sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo')
    sumo_cmd = [sumo_binary, "-c", f'files/simulations/{simulation_dir}/osm.sumocfg']
    
    traci.start(sumo_cmd)
    if not os.path.isfile(f'files/dump/{dump_name}.json'):
        start = time.perf_counter()
        data = Data(dump_name, traci.simulation.getNetBoundary(), areas_number, simulation_dir)
        data.init_grid()
        data.add_data_to_areas() 
        data.save()
        
        loading_time = round(time.perf_counter() - start, 2)
        print(f'Data loaded ({loading_time}s)')
        print(f'Dump {dump_name} created')
    else:
        print(f'Dump with name {dump_name} already exist') 
        
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
        if (args.simulation_dir is not None) and (args.areas is not None): 
            create_dump(args.new_dump, args.simulation_dir, args.areas)
    
    if args.run is not None:
        dump_path = f'files/dump/{args.run}.json'
        if os.path.isfile(dump_path):
            with open(dump_path, 'r') as f:
                data = jsonpickle.decode(f.read())
            
            process = []
            
            if args.c is not None: 
                
                # Init all process 
                for conf in args.c:  
                    
                    config = Config()  
                    config.import_config_file(conf)
                    config.init_traci(data.dir)
                    config.check_config() 
                    
                    p = RunProcess(data, config,args.save,args.csv)
                    p.init_logger()
                    process.append(p)
                    
                    p.logger.info(f'Running simulation dump "{args.run}" with the config "{conf}" ...')  
                    p.start()
                    p.join()
                    
                
if __name__ == '__main__':
    main(sys.argv[1:])
