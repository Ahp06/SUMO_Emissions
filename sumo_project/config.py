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

_SUMOCMD = 'sumo-gui'
_SUMOCFG = "mulhouse_simulation/osm.sumocfg"
CELLS_NUMBER = 10
CO2_THRESHOLD = 500000

sumo_binary = os.path.join(os.environ['SUMO_HOME'], 'bin', _SUMOCMD)
sumo_cmd = [sumo_binary, "-c", _SUMOCFG]


