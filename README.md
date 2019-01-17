# Welcome to the SUMO_Emissions wiki!

This "Proof of concept" aims to simulate the impact that connected vehicles and smart urban infrastructure would have on pollutant emissions.
Using the SUMO simulator, we developed several parameters and measures using Traci to act on the road infrastructure and vehicles.

We imagined that for a map of a given city, the city would be divided into areas, 
which when the pollution rate exceeds a certain threshold in these then we act on the infrastructure and the vehicles present in this zone.

![](https://github.com/Ahp06/SUMO_Emissions/blob/master/sumo_project/imgs/simulation_example.PNG)

# Prerequisites:
* Python 3.7
* SUMO 1.1.0

# How to run 

This application can be launched from an IDE, or from a shell (linux or Windows). 
You will need a config.json configuration file (see [default_config.json](https://github.com/Ahp06/SUMO_Emissions/blob/master/sumo_project/configs/default_config.json) for a template) and a simulation file.
You can use your own scenario file (osm.sumocfg file), see : [SUMO Tutorials](http://sumo.dlr.de/wiki/Tutorials). 

**With a Shell:**

`> py ./emissions.py [-h] [-f CONFIGFILE] [-save] [-ref] [-steps STEPS]`

* [-h] : Commands help 
* [-f CONFIGFILE] : Choose your configuration file from your working directory
* [-save] : Save the logs, by default logs will be in the logs file in the working directory with this format: 
`sumo_project/logs/sumo_logs_{current_timestamp}.log`
* [-ref] : Launch a reference simulation (without acting on infrastructure and vehicles
* [-steps STEPS] : Choose the simulated time (in seconds) 

Ex : `> py ./emissions.py -f configs/your_config.json -save -ref`



