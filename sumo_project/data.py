"""
Created on 17 oct. 2018

@author: Axel Huynh-Phuc, Thibaud Gasser
"""

"""
This module is used for loading simulation data 
"""

import argparse
import csv
import datetime
import itertools
import json
import os
import pprint
import sys
import time
import traci
from typing import List

import jsonpickle
from parse import search
from shapely.geometry import LineString

import actions
from config import Config
from model import Area, Vehicle, Lane, TrafficLight, Phase, Logic, Emission


class Data: 
    
    def __init__(self, map_bounds, config : Config):
        """
        Data constructor
        """
        self.map_bounds = map_bounds
        self.config = config
    
    def init_grid(self):
        """
        Initialize the grid of the loaded map from the configuration
        :param self.map_bounds: The map bounds
        :param areas_number: The number of areas
        :param window_size: The size of the acquisition window
        :return: A list of areas
        """
        from distutils.command.config import config
        self.grid = list()
        areas_number = self.config.areas_number
        window_size = self.config.window_size
        
        width = self.map_bounds[1][0] / areas_number
        height = self.map_bounds[1][1] / areas_number
        for i in range(areas_number):
            for j in range(areas_number):
                # bounds coordinates for the area : (xmin, ymin, xmax, ymax)
                ar_bounds = ((i * width, j * height), (i * width, (j + 1) * height),
                             ((i + 1) * width, (j + 1) * height), ((i + 1) * width, j * height))
                name = 'Area ({},{})'.format(i, j)
                area = Area(ar_bounds, name, window_size)
                self.grid.append(area)
                traci.polygon.add(area.name, ar_bounds, (255, 0, 0))  # Add polygon for UI
        return self.grid
    
    def get_all_lanes(self) -> List[Lane]:
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
    
    def parse_phase(self, phase_repr):
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
    
    def add_data_to_areas(self):
        """
        Adds all recovered data to different areas
        :param areas: The list of areas
        :return:
        """
        lanes = self.get_all_lanes()
        for area in self.grid:
            for lane in lanes:  # add lanes 
                if area.rectangle.intersects(lane.polygon):
                    area.add_lane(lane)
                    for tl_id in traci.trafficlight.getIDList():  # add traffic lights 
                        if lane.lane_id in traci.trafficlight.getControlledLanes(tl_id):
                            logics = []
                            for l in traci.trafficlight.getCompleteRedYellowGreenDefinition(tl_id):  # add logics 
                                phases = []
                                for phase in traci.trafficlight.Logic.getPhases(l):  # add phases to logics
                                    phases.append(self.parse_phase(phase.__repr__()))
                                logics.append(Logic(l, phases))
                            area.add_tl(TrafficLight(tl_id, logics))
                            
    def save(self, dump_name):
        """
        Save simulation data into a json file 
        :param dump_name: The name of your data dump
        :return:
        """
        dump_dir = 'files/dump'
        if not os.path.exists(dump_dir):
            os.mkdir(dump_dir)
        
        s = json.dumps(json.loads(jsonpickle.encode(self)), indent=4)  # for pretty JSON 
        with open(f'{dump_dir}/{dump_name}.json', 'w') as f:
            f.write(s)
        
