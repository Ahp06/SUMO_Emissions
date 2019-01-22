'''
Created on 19 janv. 2019

@author: Axel Huynh-Phuc
'''

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
    
    def __init__(self, data : Data, config : Config, save_logs, csv_export):
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

        if not os.path.exists('files/logs'):
            os.makedirs('logs')

        conf_name = self.config.config_filename.replace('.json', '')
        log_filename = f'files/logs/{self.data.dump_name}_{conf_name}_{current_date}.log'

        self.logger = logging.getLogger(f'{self.data.dir}_{conf_name}')
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
        csv_dir = 'files/csv'
        if not os.path.exists(csv_dir):
            os.mkdir(csv_dir)
    
        now = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        conf_name = self.config.config_filename.replace('.json', '')

        with open(f'files/csv/{self.data.dump_name}_{conf_name}_{now}.csv', 'w') as f:
            writer = csv.writer(f)
            # Write CSV headers
            writer.writerow(itertools.chain(('Step',), (a.name for a in self.data.grid)))
            # Write all areas emission value for each step
            for step in range(self.config.n_steps):
                em_for_step = (f'{a.emissions_by_step[step].value():.3f}' for a in self.data.grid)
                writer.writerow(itertools.chain((step,), em_for_step))
        
    def run(self):
        """
        Run a data set
        """
        try:
            self.init_logger()
            self.logger.info(f'Running simulation dump "{self.data.dump_name}" with the config "{self.config.config_filename}" ...')  
            
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
                    
            if not self.config.without_actions_mode:  # If it's not a simulation without actions
                ref = self.config.get_ref_emissions()
                if not (ref is None):  # If a reference value exist (add yours into config.py)
                    global_diff = (ref.value() - total_emissions.value()) / ref.value()
                    self.logger.info(f'Global reduction percentage of emissions = {global_diff * 100} %')
                    self.logger.info(f'-> CO2 emissions = {emissions.get_reduction_percentage(ref.co2, total_emissions.co2)} %')
                    self.logger.info(f'-> CO emissions = {emissions.get_reduction_percentage(ref.co, total_emissions.co)} %')
                    self.logger.info(f'-> Nox emissions = {emissions.get_reduction_percentage(ref.nox, total_emissions.nox)} %')
                    self.logger.info(f'-> HC emissions = {emissions.get_reduction_percentage(ref.hc, total_emissions.hc)} %')
                    self.logger.info(f'-> PMx emissions = {emissions.get_reduction_percentage(ref.pmx, total_emissions.pmx)} %')    
                
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
                        help='Run a simulation process with the dump chosen')
    parser.add_argument("-c", "--c", metavar =('config1','config2'), nargs='+', type=str,
                        help='Choose your(s) configuration file(s) from your working directory')
    parser.add_argument("-save", "--save", action="store_true",
                        help='Save the logs into the logs folder')
    parser.add_argument("-csv", "--csv", action="store_true",
                        help="Export all data emissions into a CSV file")
   
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
                for conf in args.c: # Initialize all process   
                    
                    config = Config(conf,data)  
                    p = RunProcess(data, config,args.save,args.csv)
                    process.append(p)                    
                    p.start()
                    
                for p in process : p.join()
                    
                
if __name__ == '__main__':
    main(sys.argv[1:])
