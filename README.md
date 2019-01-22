# SUMO Emissions

This "Proof of concept" aims to simulate the impact that connected vehicles and smart urban infrastructure would have on pollutant emissions.
Using the SUMO simulator, we developed several parameters and measures using Traci to act on the road infrastructure and vehicles.

We imagined that for a map of a given city, the city would be divided into areas, 
which when the pollution rate exceeds a certain threshold in these then we act on the infrastructure and the vehicles present in this zone.

![](https://github.com/Ahp06/SUMO_Emissions/blob/master/sumo_project/files/imgs/simulation_example.PNG)

# Prerequisites:
* Python >3.7 : https://www.python.org/downloads/
* External Python librairies : shapely, parse, jsonpickle : ``` > pip install [LIBRARY_NAME] ```
* SUMO 1.1.0 : http://sumo.dlr.de/wiki/Downloads

# How to run 

This application can be launched from an IDE, or from a shell (linux or Windows). 
You will need a config.json configuration file (see [default_config.json](https://github.com/Ahp06/SUMO_Emissions/blob/master/sumo_project/configs/default_config.json) for a template) and a simulation file.
You can use your own scenario file (osm.sumocfg file), see : [SUMO Tutorials](http://sumo.dlr.de/wiki/Tutorials). 

**With a Shell:**

![](https://github.com/Ahp06/SUMO_Emissions/blob/master/sumo_project/files/imgs/runner_help.PNG)

Create a data dump from simulation directory : 

![](https://github.com/Ahp06/SUMO_Emissions/blob/master/sumo_project/files/imgs/runner_new_dump.PNG)

This command will create new dump called "dump" from the simulation directory "mysimulationdir" with a 10x10 grid. 

Run simulations in parallel with multiple configuration files : 

![](https://github.com/Ahp06/SUMO_Emissions/blob/master/sumo_project/files/imgs/runner_run_ex.PNG)

This command will run a simulation dump "dump" with the configuration file(s) "config1" and "config2" 
with CSV data export and logs backup.
