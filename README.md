# SUMO Emissions

This "Proof of concept" aims to simulate the impact that connected vehicles and smart urban infrastructure would have on pollutant emissions.
Using the SUMO simulator, we developed several parameters and measures using Traci to act on the road infrastructure and vehicles.

We imagined that for a map of a given city, the city would be divided into areas, 
which when the pollution rate exceeds a certain threshold in these then we act on the infrastructure and the vehicles present in this zone.

![](https://github.com/Ahp06/SUMO_Emissions/blob/master/sumo_project/files/imgs/simulation_example.PNG)

# Prerequisites:
* Python >3.7 : https://www.python.org/downloads/
* External Python librairies : shapely, parse, jsonpickle : ``` > pip install [LIBRARY_NAME] ```
* SUMO 1.0.0 : http://sumo.dlr.de/wiki/Downloads

# How to run 

This application can be launched from an IDE, or from a shell (linux, Windows, MacOS). 
You will need a config.json configuration file (see [default_config.json](https://github.com/Ahp06/SUMO_Emissions/wiki/Configuration-file) for a template) and a simulation file.
You can use your own scenario file (osm.sumocfg file), see : [SUMO Tutorials](http://sumo.dlr.de/wiki/Tutorials). 

**With a Shell:**

```
usage: runner.py [-h] [-new_dump NEW_DUMP] [-areas AREAS]
                 [-simulation_dir SIMULATION_DIR] [-run RUN]
                 [-c config1 [config2 ...]] [-c_dir C_DIR] [-save] [-csv]

optional arguments:
  -h, --help            show this help message and exit
  -new_dump NEW_DUMP, --new_dump NEW_DUMP
                        Load and create a new data dump with the configuration
                        file chosen
  -areas AREAS, --areas AREAS
                        Will create a grid with "areas x areas" areas
  -simulation_dir SIMULATION_DIR, --simulation_dir SIMULATION_DIR
                        Choose the simulation directory
  -run RUN, --run RUN   Run a simulation process with the dump chosen
  -c config1 [config2 ...], --c config1 [config2 ...]
                        Choose your(s) configuration file(s) from your working
                        directory
  -c_dir C_DIR, --c_dir C_DIR
                        Choose a directory which contains your(s)
                        configuration file(s)
  -save, --save         Save the logs into the logs folder
  -csv, --csv           Export all data emissions into a CSV file
```

Create a data dump from simulation directory : 

```py ./runner.py -new_dump dump -areas 10 -simulation_dir [PATH_TO_SIMUL_DIR]```

This command will create new dump called "dump" from the simulation directory chosen with a 10x10 grid. 

Run simulations in parallel with multiple configuration files : 

```py ./runner.py -run dump -c [PATH_TO_CONFIG1] [PATH_TO_CONFIG2] -save -csv```

This command will run a simulation dump "dump" with the configuration file(s) "config1" and "config2" 
with CSV data export and logs backup.

From a folder which contains multiple configuration files : 

```py ./runner.py -run dump -c_dir [PATH_TO_CONFIG_DIR] -save -csv```

Log and csv files will be written in a sub folder of the simulation folder.  


