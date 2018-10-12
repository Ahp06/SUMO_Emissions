'''
Created on 11 oct. 2018

@author: Axel HUYNH-PHUC
'''

import os, sys
import traci
from traci import polygon

'''Launch traci'''
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:   
    sys.exit("please declare environment variable 'SUMO_HOME'")
    
sumoBinary = "C:\\Users\\Admin\\AppData\\Roaming\\Microsoft\\Installer\\{A63B306E-2B15-11E1-88C8-028037EC0200}\\sumogui.exe"
sumoCmd = [sumoBinary, "-c", "mulhouse_simulation\\osm.sumocfg"]
traci.start(sumoCmd) 

'''Variables and constants declaration'''
cells_step = 10
boundary = traci.simulation.getNetBoundary()
areas = [[0] * cells_step for _ in range(cells_step)]
emissionsArea = [[0] * cells_step for _ in range(cells_step)]
width = boundary[1][0] / cells_step  # width/step
height = boundary[1][1] / cells_step  # height/step 
CO2_threshold = 500000


'''creating multiple zones of equal sizes'''
def init_grid():
    default_color = (0, 255, 0) 
    for i in range(cells_step):
        for j in range(cells_step):
            area = ((i * width, j * height), (i * width, (j + 1) * height),
                      ((i + 1) * width, (j + 1) * height), ((i + 1) * width, j * height))
            areas[i][j] = area
            polygon.add("area " + str(i) + "," + str(j), area, default_color, False, "rectangle")
            

'''Emissions recovery by area'''
def getEmissionsByArea(i, j):
    vehicles = []
    '''Vehicle IDs retrieving into this area'''
    for veh_id in traci.vehicle.getIDList():
        pos = traci.vehicle.getPosition(veh_id)
        if((i * width < pos[0] and (i + 1) * width > pos[0]) 
            and (j * height < pos[1] and (j + 1) * height > pos[1])):
            vehicles.append(veh_id)
            
    '''Sum all emissions'''
    emissions = 0.0
    for veh_id in vehicles:
        emission = traci.vehicle.getCO2Emission(veh_id)
        emissions += emission 
    
    '''Change area color if emisssions exceeds the threshold'''
    emissionsArea[i][j] += emissions
    if(emissionsArea[i][j] >= CO2_threshold):
        red = (255, 0, 0)
        polygon.setColor("area " + str(i) + "," + str(j), red)
        polygon.setFilled("area " + str(i) + "," + str(j), True)

'''Recover emissions from all areas'''
def getAllEmissions():
    for i in range(cells_step):
        for j in range(cells_step):
            getEmissionsByArea(i, j)

'''Display emissions information'''
def showEmissions():
    for i in range(cells_step):
        for j in range(cells_step):
            print("Total CO2 emissions into Area " + str(i) + "," + str(j) 
                  + " = " , str(emissionsArea[i][j]) + " mg" )
            

'''Simulation launch'''
step = 0
init_grid()      
while step < 100:  # while traci.simulation.getMinExpectedNumber() > 0: 
    traci.simulationStep()
    getAllEmissions()
    step += 1

'''Display emissions information and close simulation'''
showEmissions()
traci.close()
sys.stdout.flush()

