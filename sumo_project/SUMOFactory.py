'''
Created on 17 oct. 2018

@author: Admin
'''
import os, sys
import traci 
from shapely.geometry import Polygon
from shapely.geometry import Point
from shapely.geometry.linestring import LineString


class SUMOFactory(object):
    
    def __init__(self):
        '''Constructor'''
    
    def stopVehicle(self, veh_id):
        traci.vehicle.remove(veh_id, traci.constants.REMOVE_PARKING)
        
    def getLanesIntoArea(self, area):
        polygon_area = Polygon(area)
        lanes = []
        for lane_id in traci.lane.getIDList():
            polygon_lane = LineString(traci.lane.getShape(lane_id))
            if polygon_area.intersects(polygon_lane):
                print("lane is in area : ", polygon_lane)
                lanes.append(lane_id)
        return lanes
           
    def lock_area(self, area):
        lanes = self.getLanesIntoArea(area)
        for lane_id in lanes:
            '''print("Vehicles number into lane =  ", traci.lane.getLastStepVehicleNumber(lane_id))
            if traci.lane.getLastStepVehicleNumber(lane_id) == 0:
                traci.lane.setDisallowed(lane_id, "passenger")
                print("lane blocked : ", lane_id)'''
            traci.lane.setMaxSpeed(lane_id, 30) 
            for veh_id in traci.vehicle.getIDList(): 
                traci.vehicle.rerouteTraveltime(veh_id, True)
