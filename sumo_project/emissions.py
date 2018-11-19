from typing import List

import traci
from shapely.geometry import LineString

import actions
import config
import sys
from model import Area, Vehicle, Lane

areas = list()

def init_grid(simulation_bounds, cells_number):
    width = simulation_bounds[1][0] / cells_number
    height = simulation_bounds[1][1] / cells_number
    for i in range(cells_number):
        for j in range(cells_number):
            # bounds coordinates for the area : (xmin, ymin, xmax, ymax)
            ar_bounds = ((i * width, j * height), (i * width, (j + 1) * height),
                         ((i + 1) * width, (j + 1) * height), ((i + 1) * width, j * height))
            area = Area(ar_bounds)
            area.name = 'area {}/{}'.format(i, j)
            areas.append(area)
            traci.polygon.add(area.name, ar_bounds, (0, 255, 0))
    return areas


def get_all_vehicles() -> List[Vehicle]:
    vehicles = list()
    for veh_id in traci.vehicle.getIDList():
        veh_pos = traci.vehicle.getPosition(veh_id)
        vehicle = Vehicle(veh_id, veh_pos)
        vehicle.co2 = traci.vehicle.getCO2Emission(vehicle.veh_id)
        vehicles.append(vehicle)
    return vehicles


def get_all_lanes() -> List[Lane]:
    lanes = []
    for lane_id in traci.lane.getIDList():
        polygon_lane = LineString(traci.lane.getShape(lane_id))
        lanes.append(Lane(lane_id, polygon_lane))
    return lanes


def get_emissions(grid: List[Area], vehicles: List[Vehicle]):
    for area in grid:
        for vehicle in vehicles:
            if vehicle.pos in area:
                area.emissions += vehicle.co2
        if area.emissions > config.CO2_THRESHOLD and area.locked == False:
            actions.lock_area(area, vehicles)
            traci.polygon.setColor(area.name, (255, 0, 0))
            traci.polygon.setFilled(area.name, True)


def add_lanes_to_areas(areas: List[Area]):
    lanes = get_all_lanes()
    for area in areas:
        for lane in lanes:
            if area.rectangle.intersects(lane.polygon):
                area.add_lane(lane)


def main():
    try:
        traci.start(config.sumo_cmd)
        grid = init_grid(traci.simulation.getNetBoundary(), config.CELLS_NUMBER)
        add_lanes_to_areas(grid)
        
        step = 0 
        while step < config.n_steps : #traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            
            vehicles = get_all_vehicles()
            get_emissions(grid, vehicles)
            #actions.adjustEdgesWeight()

            
            step += 1 
            sys.stdout.write(f'Simulation step =  {step}/{config.n_steps}'+'\r')
            sys.stdout.flush()
            
    finally:
        total_emissions = 0 
        for area in areas:
            total_emissions += area.emissions
        
        #For 200 steps, total emissions = 42816869.054364316 mg
        #For 400 steps, total emissions = 136020579.71122485 mg
        
        print(f'\n**** Total emissions (CO2) = {total_emissions} mg')
        diff_with_lock = (136020579.71122485 - total_emissions)/136020579.71122485
        print(f'**** Reduction percentage of CO2 emissions = {diff_with_lock*100} % ****\n')
        
        traci.close(False)


if __name__ == '__main__':
    main()
