"""
This module defines the entry point of the application
"""

import argparse
import csv
import datetime
import itertools
import logging
import multiprocessing
import os
import sys
import time
import traci

import jsonpickle

from config import Config
from data import Data
import emissions
from model import Emission


"""
Init the Traci API
"""
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")
    
class RunProcess(multiprocessing.Process):
    """
    Run process inheriting from multiprocessing.Process
    """
    
    def __init__(self, data: Data, config: Config, save_logs: bool, csv_export: bool):
        """
        RunProcess constructor
        :param data: The data instance
        :param config: The config instance
        :param save_logs: If save_logs == True, it will save the logs into the logs directory 
        :param csv_export: If csv_export == True, it will export all emissions data into a csv file 
        """
        multiprocessing.Process.__init__(self)
        self.data = data 
        self.config = config
        self.save_logs = save_logs
        self.csv_export = csv_export
        
    def init_logger(self):
        """
        Init logger properties 
        """
        now = datetime.datetime.now()
        current_date = now.strftime("%Y_%m_%d_%H_%M_%S")
        
        logdir = f'{self.data.dir}/logs/'
        logging.info(logdir)
        if not os.path.exists(logdir):
            os.mkdir(logdir)

        conf_name = self.config.config_filename.replace('.json', '')
        log_filename = f'{logdir}/{current_date}.log'

        self.logger = logging.getLogger(f'sumo_logger')
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        if self.save_logs:
            file_handler = logging.FileHandler(log_filename)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def export_data_to_csv(self):
        """
        Export all Emission objects as a CSV file into the csv directory
        """
        csv_dir = f'{self.data.dir}/csv'
        if not os.path.exists(csv_dir):
            os.mkdir(csv_dir)
    
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        conf_name = self.config.config_filename.replace('.json', '')

        csvfile = os.path.join(csv_dir, f'{self.data.dump_name}_{conf_name}_{now}.csv')
        with open(csvfile, 'w') as f:
            writer = csv.writer(f)
            # Write CSV headers
            writer.writerow(itertools.chain(('Step',), (a.name for a in self.data.grid)))
            # Write all areas emission value for each step
            for step in range(self.config.n_steps):
                em_for_step = (f'{a.emissions_by_step[step].value():.3f}' for a in self.data.grid)
                writer.writerow(itertools.chain((step,), em_for_step))
        
    def run(self):
        """
        Launch a simulation, will be called when a RunProcess instance is started
        """
        try:
            self.init_logger()
            self.logger.info(f'Running simulation dump "{self.data.dump_name}" with the config "{self.config.config_filename}" ...')  
            
            if self.config.without_actions_mode:
                self.logger.info('Reference simulation')
            
            traci.start(self.config.sumo_cmd)
            
            for area in self.data.grid:  # Set acquisition window size 
                area.set_window_size(self.config.window_size)
                traci.polygon.add(area.name, area.rectangle.exterior.coords, (255, 0, 0))  # Add polygon for UI
                
            self.logger.info(f'Loaded simulation file : {self.config._SUMOCFG}')
            self.logger.info('Loading data for the simulation')
            
            start = time.perf_counter()
            self.logger.info('Simulation started...')
            step = 0
            while step < self.config.n_steps:
                traci.simulationStep()
        
                vehicles = emissions.get_all_vehicles()
                emissions.get_emissions(self, vehicles, step)
                step += 1
        
                print(f'step = {step}/{self.config.n_steps}', end='\r')
        
        finally:
            traci.close(False)
            
            total_emissions = Emission()
            for area in self.data.grid:
                total_emissions += area.sum_all_emissions()
                
            self.logger.info(f'Total emissions = {total_emissions.value()} mg')
            for pollutant in ['co2','co','nox','hc','pmx']:
                value = total_emissions.__getattribute__(pollutant)
                self.logger.info(f'{pollutant.upper()} = {value} mg')
                
            simulation_time = round(time.perf_counter() - start, 2)
            self.logger.info(f'End of the simulation ({simulation_time}s)')
            
            # 1 step is equal to one second simulated
            self.logger.info(f'Real-time factor : {self.config.n_steps / simulation_time}')
            
            if self.csv_export:
                self.export_data_to_csv()
                self.logger.info(f'Exported data into the csv folder')
                
def create_dump(dump_name, simulation_dir, areas_number):
    """
    Create a new dump with config file and dump_name chosen 
    :param dump_name: The name of the data dump
    :param simulation_dir: The simulation directory 
    :param areas_number: The number of areas in grid 
    :return:
    """
    
    #sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo')
    #sumo_cmd = [sumo_binary, "-c", f'files/simulations/{simulation_dir}/osm.sumocfg']
    
    for f in os.listdir(simulation_dir):
        if f.endswith('.sumocfg'):
            _SUMOCFG = os.path.join(simulation_dir, f)
            
    sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo')
    sumo_cmd = [sumo_binary, "-c", _SUMOCFG]
    
    
    traci.start(sumo_cmd)
    if not os.path.isfile(f'{simulation_dir}/dump/{dump_name}.json'):
        start = time.perf_counter()
        data = Data(dump_name, traci.simulation.getNetBoundary(), areas_number, simulation_dir)
        data.init_grid()
        data.add_data_to_areas() 
        data.save()
        
        loading_time = round(time.perf_counter() - start, 2)
        print(f'Data loaded ({loading_time}s)')
        print(f'Dump {dump_name} created')
    else:
        print(f'Dump with name {dump_name} already exists')
        
    traci.close(False)  
    
def add_options(parser):
    """
    Add command line options
    :param parser: The command line parser
    :return:
    """
     
    parser.add_argument("-new_dump", "--new_dump", type=str,
                        help='Load and create a new data dump with the configuration file chosen')
    parser.add_argument("-areas", "--areas", type=int,
                        help='Will create a grid with "areas x areas" areas')
    parser.add_argument("-simulation_dir", "--simulation_dir", type=str,
                        help='Choose the simulation directory')
    
    parser.add_argument("-run", "--run", type=str,
                        help='Run a simulation process with the dump chosen')
    parser.add_argument("-c", "--c", metavar =('config1','config2'), nargs='+', type=str,
                        help='Choose your(s) configuration file(s) from your working directory')
    parser.add_argument("-c_dir", "--c_dir", type=str,
                        help='Choose a directory which contains your(s) configuration file(s)')
    parser.add_argument("-save", "--save", action="store_true",
                        help='Save the logs into the logs folder')
    parser.add_argument("-csv", "--csv", action="store_true",
                        help="Export all data emissions into a CSV file")
   
def check_user_entry(args):
    """
    Check the user entry consistency
    """
    if (args.new_dump is not None):
        if(args.areas is None or args.simulation_dir is None):
            print('The -new_dump argument requires the -areas and -simulation_dir options')
            return False
        
    if (args.run is not None):
        if(args.c is None and args.c_dir is None):
            print('The -run argument requires the -c or -c_dir')
            return False
    
    return True 
    
def main(args):
    """
    The entry point of the application
    :param args: Command line options
    :return:
    """
    parser = argparse.ArgumentParser()
    add_options(parser)
    args = parser.parse_args(args)
    
    if(check_user_entry(args)):
        
        if args.new_dump is not None:
            if (args.simulation_dir is not None) and (args.areas is not None): 
                create_dump(args.new_dump, args.simulation_dir, args.areas)
        
        if args.run is not None:
            dump_path = f'{args.run}'
            if os.path.isfile(dump_path):
                with open(dump_path, 'r') as f:
                    data = jsonpickle.decode(f.read())
                
                process = []
                files = [] 
                
                if args.c is not None: 
                    for config in args.c:
                        files.append(f'{config}') 
                
                if args.c_dir is not None: 
                    path = f'{args.c_dir}'
                    bundle_files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))] 
                    for config in bundle_files:
                        files.append(os.path.join(path, config))

                for conf in files: # Initialize all process
                    config = Config(conf,data)  
                    p = RunProcess(data, config, args.save, args.csv)
                    process.append(p)                    
                    p.start()
                        
                for p in process : p.join() 
                
if __name__ == '__main__':
    main(sys.argv[1:])
