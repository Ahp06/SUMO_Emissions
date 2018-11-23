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

lock_mode = True
routing_mode = False

sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', _SUMOCMD)
sumo_cmd = [sumo_binary, "-c", _SUMOCFG]

def showConfig():
    return (str(f'Grid : {CELLS_NUMBER}x{CELLS_NUMBER}\n')
    + str(f'step number = {n_steps}\n')
    + str(f'lock mode = {lock_mode}\n')
    + str(f'routing mode = {routing_mode}\n'))
    
