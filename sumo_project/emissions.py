import traci
import config

from SUMOFactory import SUMOFactory
from model import Area


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


def emission_for_area(area):
    # retrieve all vehicles into this area
    for veh_id in traci.vehicle.getIDList():
        pos = traci.vehicle.getPosition(veh_id)
        if pos in area:
            area.emissions += traci.vehicle.getCO2Emission(veh_id)


def get_emissions(areas, factory):
    for area in areas:
        emission_for_area(area)
        if area.emissions > config.CO2_THRESHOLD:
            # print(f'Threshold exceeded in {area.name} : {area.emissions}')
            factory.lock_area(area)
            traci.polygon.setColor(area.name, (255, 0, 0))
            traci.polygon.setFilled(area.name, True)


def main():
    try:
        traci.start(config.sumo_cmd)
        grid = init_grid(traci.simulation.getNetBoundary(), config.CELLS_NUMBER)
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            get_emissions(grid, SUMOFactory())
    finally:
        traci.close(False)


if __name__ == '__main__':
    main()
