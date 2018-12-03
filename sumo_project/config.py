"""
Global configuration for the simulation
"""

import os
import sys

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

_SUMOCMD = 'sumo' # use 'sumo-gui' cmd for UI 
_SUMOCFG = "mulhouse_simulation/osm.sumocfg"
CELLS_NUMBER = 10
EMISSIONS_THRESHOLD = 500000
n_steps = 200 

#Vehicles are routed according to the less polluted route
weight_routing_mode = False

#Limit the speed into areas when the threshold is exceeded
limited_speed = 30
limit_speed_mode = True

#Decrease all traffic lights duration into the area when the threshold is exceeded
rf_trafficLights_duration = 0.2
adjust_traffic_light_mode = True

#Weight routing mode cannot be combinated with other actions 
if weight_routing_mode:
    limit_speed_mode = False
    adjust_traffic_light_mode = False

sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', _SUMOCMD)
sumo_cmd = [sumo_binary, "-c", _SUMOCFG]

def showConfig():
    return (str(f'Grid : {CELLS_NUMBER}x{CELLS_NUMBER}\n')
    + str(f'step number = {n_steps}\n')
    + str(f'limit speed mode = {limit_speed_mode}\n')
    + str(f'weight routing mode= {weight_routing_mode}\n')
    + str(f'adjust traffic light mode = {adjust_traffic_light_mode} , RF = {rf_trafficLights_duration}\n'))
    
