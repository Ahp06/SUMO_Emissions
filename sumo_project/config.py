"""
Global configuration for the simulation
"""

import datetime
import logging
import os
import sys
import json

class Config: 
    
    # Total of emissions of all pollutants in mg for n steps of simulation without locking areas
    # These constants are simulation dependant, you must change them according to your simulation 
    total_emissions100 = 13615949.148296086
    total_emissions200 = 43970763.15084738
    total_emissions300 = 87382632.0821697
    
    def __init__(self):
        '''Default constructor'''
        
    def import_config_file(self,config_file):
        with open(config_file,'r') as f:
            data = json.load(f)
            
        self._SUMOCMD = data["_SUMOCMD"]
        self._SUMOCFG = data["_SUMOCFG"]
        
        self.areas_number = data["areas_number"]
        self.emissions_threshold = data["emissions_threshold"]
        self.n_steps = data["n_steps"]
        self.window_size = data["window_size"]
        
        self.without_actions_mode = data["without_actions_mode"]
        self.limit_speed_mode = data["limit_speed_mode"]
        self.speed_rf = data["speed_rf"]
        self.adjust_traffic_light_mode = data["adjust_traffic_light_mode"]
        self.trafficLights_duration_rf = data["trafficLights_duration_rf"]
        self.weight_routing_mode = data["weight_routing_mode"]
        self.lock_area_mode = data["lock_area_mode"]
            
        self.check_config()
                
    def check_config(self):
        #Weight routing mode cannot be combinated with other actions 
        if self.weight_routing_mode:
            self.limit_speed_mode = False
            self.adjust_traffic_light_mode = False
            self.lock_area_mode = False
                
        #If without_actions_mode is choosen 
        if self.without_actions_mode:
            self.limit_speed_mode = False
            self.adjust_traffic_light_mode = False
            self.weight_routing_mode = False
            self.lock_area_mode = False
        
                
    def __repr__(self) -> str:
        return (str(f'grid : {self.areas_number}x{self.areas_number}\n')
        + str(f'step number = {self.n_steps}\n')
        + str(f'window size = {self.window_size}\n')
        + str(f'weight routing mode = {self.weight_routing_mode}\n')
        + str(f'lock area mode = {self.lock_area_mode}\n')
        + str(f'limit speed mode = {self.limit_speed_mode}, RF = {self.speed_rf*100}%\n')
        + str(f'adjust traffic light mode = {self.adjust_traffic_light_mode} , RF = {self.trafficLights_duration_rf*100}%\n'))
                
    
    def init_traci(self):
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            sys.exit("please declare environment variable 'SUMO_HOME'")
        
        sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', self._SUMOCMD)
        self.sumo_cmd = [sumo_binary, "-c", self._SUMOCFG]
    
    def init_logger(self, save_logs = True):
        now = datetime.datetime.now()
        current_date = now.strftime("%Y_%m_%d_%H_%M_%S")
        
        if not os.path.exists('logs'):
            os.makedirs('logs')
    
        log_filename = f'logs/sumo_logs_{current_date}.log'
        
        logger = logging.getLogger("sumo_logger")
        logger.setLevel(logging.INFO)
        if save_logs :
            handler = logging.FileHandler(log_filename)
        else: 
            handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def get_basics_emissions(self):
        if self.n_steps == 100:
            return self.total_emissions100
        if self.n_steps == 200:
            return self.total_emissions200
        if self.n_steps == 300:
            return self.total_emissions300
    
    
