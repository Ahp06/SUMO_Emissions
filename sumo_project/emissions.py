from typing import List

import traci

import config
from model import Area, Vehicle


def init_grid(simulation_bounds, cells_number):
    width = simulation_bounds[1][0] / cells_number
    height = simulation_bounds[1][1] / cells_number
    # TODO: change data structure?
    areas = list()
    for i in range(cells_number):
        for j in range(cells_number):
            # bounds coordinates for the area : (xmin, ymin, xmax, ymax)
            ar_bounds = ((i * width, j * height), (i * width, (j + 1) * height),
                         ((i + 1) * width, (j + 1) * height), ((i + 1) * width, j * height))
            area = Area(ar_bounds)
            area.name = 'area{}{}'.format(i, j)
            areas.append(area)
            traci.polygon.add(area.name, ar_bounds, (0, 255, 0))
    return areas


def get_all_vehicles() -> List[Vehicle]:
    vehicles = list()
    for veh_id in traci.vehicle.getIDList():
        veh_pos = traci.vehicle.getPosition(veh_id)
        vehicle = Vehicle(veh_id, veh_pos)
        vehicle.co2 = traci.vehicle.getCO2Emission(vehicle.id)
        vehicles.append(vehicle)
    return vehicles


def get_emissions(grid: List[Area], vehicles: List[Vehicle]):
    for area in grid:
        for vehicle in vehicles:
            if vehicle.pos in area:
                area.emissions += vehicle.co2
        if area.emissions > config.CO2_THRESHOLD:
            # print(f'Threshold exceeded in {area.name} : {area.emissions}')
            # factory.lock_area(area)
            traci.polygon.setColor(area.name, (255, 0, 0))
            traci.polygon.setFilled(area.name, True)


def main():
    try:
        traci.start(config.sumo_cmd)
        grid = init_grid(traci.simulation.getNetBoundary(), config.CELLS_NUMBER)
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            # get_emissions(grid, SUMOFactory())
            vehicles = get_all_vehicles()
            get_emissions(grid, vehicles)
    finally:
        traci.close(False)


if __name__ == '__main__':
    main()
