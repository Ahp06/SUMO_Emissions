"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""

"""
This module defines the global configuration for the simulation
"""

import datetime
import json
import logging
import os
import sys

from model import Emission


class Config:
    """
    The Config class defines all simulation properties that can be changed
    """

    # Total of emissions of all pollutants in mg for n steps of simulation without acting on areas
    # These constants are simulation dependant, you must change them according to your simulation 
    ref200 = Emission(co2=42816869.05436445, co=1128465.0343051048, nox=18389.648337283958, hc=6154.330914019103,
                      pmx=885.0829265236318)

    def __init__(self):
        """
        Default constructor
        """

    def import_config_file(self, config_file):
        """
        Import your configuration file in JSON format
        :param config_file: The path to your configuration file
        :return:
        """
        with open(f'files/configs/{config_file}.json', 'r') as f:
            data = json.load(f)

        for option in data:
            self.__setattr__(option, data[option])
        self.config_filename = os.path.basename(f.name)
        self.check_config()

    def check_config(self):
        """
        Check the relevance of user configuration choices
        :return:
        """
        # Weight routing mode cannot be combined with other actions
        if self.weight_routing_mode:
            self.limit_speed_mode = False
            self.adjust_traffic_light_mode = False
            self.lock_area_mode = False

        # If without_actions_mode is chosen
        if self.without_actions_mode:
            self.limit_speed_mode = False
            self.adjust_traffic_light_mode = False
            self.weight_routing_mode = False
            self.lock_area_mode = False

    def __repr__(self) -> str:
        """
        :return: All properties chosen by the user
        """
        return (
            f'grid : {self.areas_number}x{self.areas_number}\n'
            f'step number = {self.n_steps}\n'
            f'window size = {self.window_size}\n'
            f'weight routing mode = {self.weight_routing_mode}\n'
            f'lock area mode = {self.lock_area_mode}\n'
            f'limit speed mode = {self.limit_speed_mode}, RF = {self.speed_rf * 100}%\n'
            f'adjust traffic light mode = {self.adjust_traffic_light_mode},'
            f'RF = {self.trafficLights_duration_rf * 100}%\n'
        )

    def init_traci(self):
        """
        Init the Traci API
        :return:
        """
        if 'SUMO_HOME' in os.environ:
            tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
            sys.path.append(tools)
        else:
            sys.exit("please declare environment variable 'SUMO_HOME'")

        sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', self._SUMOCMD)
        self.sumo_cmd = [sumo_binary, "-c", self._SUMOCFG]

    def init_logger(self, dump_name, save_logs=False):
        """
        Init the application logger
        :param save_logs: If save_logs is True, it will save the logs into the logs directory
        :return:
        """
        now = datetime.datetime.now()
        current_date = now.strftime("%Y_%m_%d_%H_%M_%S")

        if not os.path.exists('files/logs'):
            os.makedirs('logs')

        log_filename = f'files/logs/{dump_name}_{current_date}.log'

        logger = logging.getLogger("sumo_logger")
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        if save_logs:
            file_handler = logging.FileHandler(log_filename)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def get_ref_emissions(self):
        """
        :return: Return the sum of all emissions (in mg) from the simulation of reference
        """
        if self.n_steps == 200:
            return self.ref200
