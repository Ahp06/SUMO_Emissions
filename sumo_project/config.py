"""
Global configuration for the simulation
"""

import os
import sys
import datetime

###############################################################################
############################# SIMULATION FILE #################################
###############################################################################

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")

_SUMOCMD = 'sumo' # use 'sumo-gui' cmd for UI 
_SUMOCFG = "mulhouse_simulation/osm.sumocfg"
sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', _SUMOCMD)
sumo_cmd = [sumo_binary, "-c", _SUMOCFG]

###############################################################################
############################# LOGS OUTPUT #####################################
###############################################################################

now = datetime.datetime.now()
current_date = now.strftime("%Y_%m_%d_%H_%M_%S")
LOG_FILENAME = f'sumo_logs_{current_date}.log'

###############################################################################
########################## SIMULATION CONFIGURATION ###########################
###############################################################################

CELLS_NUMBER = 10
EMISSIONS_THRESHOLD = 500000
n_steps = 200 

###############################################################################
########################## ACTIONS CONFIGURATION ##############################
###############################################################################

#Set this mode to True if you want running a basic simulation without actions 
without_actions_mode = False 

#Limit the speed into areas when the threshold is exceeded
speed_rf = 0.1
limit_speed_mode = True

#Decrease all traffic lights duration into the area when the threshold is exceeded
trafficLights_duration_rf = 0.2
adjust_traffic_light_mode = True

#Vehicles are routed according to the less polluted route (HEAVY)
weight_routing_mode = False

#Lock the area when the threshold is exceeded (NOT FIXED)
lock_area_mode = False 

#Weight routing mode cannot be combinated with other actions 
if weight_routing_mode:
    limit_speed_mode = False
    adjust_traffic_light_mode = False
    
#If without_actions_mode is choosen 
if without_actions_mode:
    limit_speed_mode = False
    adjust_traffic_light_mode = False
    weight_routing_mode = False
    lock_area_mode = False

###############################################################################
########################## SIMULATION REFERENCES ##############################
###############################################################################

# Total of emissions of all pollutants in mg for n steps of simulation without locking areas
total_emissions200 = 43970763.15084749  
total_emissions300 = 87382632.08217141
total_emissions400 = 140757491.8489904
total_emissions500 = 202817535.43856794

###############################################################################
########################## CONFIGURATION METHODS ##############################
###############################################################################

def get_basics_emissions():
    if n_steps == 200:
        return total_emissions200
    if n_steps == 300:
        return total_emissions300
    if n_steps == 400:
        return total_emissions400
    if n_steps == 500:
        return total_emissions500

def show_config():
    return (str(f'Grid : {CELLS_NUMBER}x{CELLS_NUMBER}\n')
    + str(f'step number = {n_steps}\n')
    + str(f'weight routing mode = {weight_routing_mode}\n')
    + str(f'lock area mode = {lock_area_mode}\n')
    + str(f'limit speed mode = {limit_speed_mode}, RF = {speed_rf*100}%\n')
    + str(f'adjust traffic light mode = {adjust_traffic_light_mode} , RF = {trafficLights_duration_rf*100}%\n'))
    
