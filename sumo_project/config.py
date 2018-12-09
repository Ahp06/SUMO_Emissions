"""
Global configuration for the simulation
"""

import datetime
import logging
import os
import sys


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
################################## LOGS #######################################
###############################################################################

now = datetime.datetime.now()
current_date = now.strftime("%Y_%m_%d_%H_%M_%S")
log_filename = f'logs/sumo_logs_{current_date}.log'

# create logger
logger = logging.getLogger("sumo_logger")
logger.setLevel(logging.INFO)
# create handler and set level to info
handler = logging.FileHandler(log_filename)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to handler
handler.setFormatter(formatter)
# add handler to logger
logger.addHandler(handler)

###############################################################################
########################## SIMULATION CONFIGURATION ###########################
###############################################################################

areas_number = 10 # Simulation boundary will be divided into areas_number x areas_number areas 
emissions_threshold = 500000
n_steps = 200 
window_size = 100

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
    lock_area_mode = False
    
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
# These constants are simulation dependant, you must change them according to your simulation 
total_emissions100 = 13615949.148296086
total_emissions200 = 43970763.15084738
total_emissions300 = 87382632.0821697

###############################################################################
########################## CONFIGURATION METHODS ##############################
###############################################################################

def get_basics_emissions():
    if n_steps == 100:
        return total_emissions100
    if n_steps == 200:
        return total_emissions200
    if n_steps == 300:
        return total_emissions300

def show_config():
    return (str(f'Grid : {areas_number}x{areas_number}\n')
    + str(f'step number = {n_steps}\n')
    + str(f'window size = {window_size}\n')
    + str(f'weight routing mode = {weight_routing_mode}\n')
    + str(f'lock area mode = {lock_area_mode}\n')
    + str(f'limit speed mode = {limit_speed_mode}, RF = {speed_rf*100}%\n')
    + str(f'adjust traffic light mode = {adjust_traffic_light_mode} , RF = {trafficLights_duration_rf*100}%\n'))
    
