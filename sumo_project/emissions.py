from typing import List

import traci
from shapely.geometry import LineString

import actions
import config
import sys
from model import Area, Vehicle, Lane , TrafficLight
from traci import trafficlight


def init_grid(simulation_bounds, cells_number):
    grid = list()
    width = simulation_bounds[1][0] / cells_number
    height = simulation_bounds[1][1] / cells_number
    for i in range(cells_number):
        for j in range(cells_number):
            # bounds coordinates for the area : (xmin, ymin, xmax, ymax)
            ar_bounds = ((i * width, j * height), (i * width, (j + 1) * height),
                         ((i + 1) * width, (j + 1) * height), ((i + 1) * width, j * height))
            area = Area(ar_bounds)
            area.name = 'area ({},{})'.format(i, j)
            grid.append(area)
            traci.polygon.add(area.name, ar_bounds, (0, 255, 0))
    return grid


def compute_vehicle_emissions(veh_id):
    return (traci.vehicle.getCOEmission(veh_id)
            + traci.vehicle.getNOxEmission(veh_id)
            + traci.vehicle.getHCEmission(veh_id)
            + traci.vehicle.getPMxEmission(veh_id)
            + traci.vehicle.getCO2Emission(veh_id))


def get_all_vehicles() -> List[Vehicle]:
    vehicles = list()
    for veh_id in traci.vehicle.getIDList():
        veh_pos = traci.vehicle.getPosition(veh_id)
        vehicle = Vehicle(veh_id, veh_pos)
        vehicle.emissions = compute_vehicle_emissions(veh_id)
        vehicles.append(vehicle)
    return vehicles


def get_all_lanes() -> List[Lane]:
    lanes = []
    for lane_id in traci.lane.getIDList():
        polygon_lane = LineString(traci.lane.getShape(lane_id))
        initial_max_speed = traci.lane.getMaxSpeed(lane_id)
        lanes.append(Lane(lane_id, polygon_lane,initial_max_speed))
    return lanes


def get_emissions(grid: List[Area], vehicles: List[Vehicle]):
    for area in grid:
        for vehicle in vehicles:
            if vehicle.pos in area:
                area.emissions += vehicle.emissions
        if config.limit_speed_mode and area.emissions > config.EMISSIONS_THRESHOLD and not area.locked:
            actions.limit_speed_into_area(area, vehicles,30)
            traci.polygon.setColor(area.name, (255, 0, 0))
            traci.polygon.setFilled(area.name, True)
            if config.adjust_traffic_light_mode:
                actions.adjust_traffic_light_phase_duration(area, 0.75)


def add_data_to_areas(areas: List[Area]):
    lanes = get_all_lanes()
    for area in areas:
        for lane in lanes: #add lanes 
            if area.rectangle.intersects(lane.polygon):
                area.add_lane(lane) 
                for tl_id in traci.trafficlight.getIDList(): #add traffic lights 
                    if lane.lane_id in traci.trafficlight.getControlledLanes(tl_id):
                        area.add_tl(TrafficLight(tl_id))
        


def main():
    grid = list()
    try:
        traci.start(config.sumo_cmd)
        grid = init_grid(traci.simulation.getNetBoundary(), config.CELLS_NUMBER)
        add_data_to_areas(grid)
                
        step = 0 
        while step < config.n_steps : #traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            vehicles = get_all_vehicles()
            get_emissions(grid, vehicles)

            if config.weight_routing_mode:
                actions.adjust_edges_weights()

            step += 1
            progress = round(step/config.n_steps*100,2)
            sys.stdout.write(f'Progress :  {progress}%'+'\r')
            sys.stdout.flush()

    finally:
        traci.close(False)

        total_emissions = 0
        for area in grid:
            total_emissions += area.emissions
        
         #Total of emissions of all pollutants in mg for 200 steps of simulation without locking areas
        total_emissions200 = 43970763.15084749  
                
        print("\n**** RESULTS ****")
        print(f'Total emissions = {total_emissions} mg')
        diff_with_lock = (total_emissions200 - total_emissions)/total_emissions200
        print(f'Reduction percentage of emissions = {diff_with_lock*100} %')
        print("With the configuration :\n" + str(config.showConfig()))
        
if __name__ == '__main__':
    main()
