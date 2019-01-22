import argparse
import os
import sys
import time
import traci
import logging
import itertools
import csv

import jsonpickle
import multiprocessing
import datetime

from config import Config
from data import Data
import emissions
from model import Emission


class RunProcess(multiprocessing.Process):
    
    def __init__(self, data : Data, config : Config, save_logs, csv_export):
        multiprocessing.Process.__init__(self)
        self.data = data 
        self.config = config
        self.save_logs = save_logs
        self.csv_export = csv_export
        
    def init_logger(self):
        now = datetime.datetime.now()
        current_date = now.strftime("%Y_%m_%d_%H_%M_%S")

        if not os.path.exists('files/logs'):
            os.makedirs('logs')

        # log_filename = f'files/logs/{logger_name}_{current_date}.log'
        log_filename = f'files/logs/{current_date}.log'

        conf_name = self.config.config_filename.replace('.json', '')
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
                
        