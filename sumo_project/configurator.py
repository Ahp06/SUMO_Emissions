# -*- coding: utf-8 -*-
import os
import sys

if 'SUMO_HOME' in os.environ:
    TOOLSDIR = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(TOOLSDIR)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")


import argparse
import datetime
import json
import logging
import shutil
import subprocess
import tempfile
import time
from sys import argv
from types import SimpleNamespace
from xml.etree import ElementTree

import randomTrips
import sumolib

# Absolute path of the directory the script is in
SCRIPTDIR = os.path.dirname(__file__)
TEMPLATEDIR = os.path.join(SCRIPTDIR, 'templates')
SUMOBIN = os.path.join(os.environ['SUMO_HOME'], 'bin')

# Init logger
logfile = os.path.join(SCRIPTDIR, f'files/logs/configurator_{datetime.datetime.utcnow().isoformat()}.log')
logging.basicConfig(
    filename=logfile,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

"""
Definition of vehicle classes. 
See http://sumo.dlr.de/wiki/Definition_of_Vehicles,_Vehicle_Types,_and_Routes#Abstract_Vehicle_Class
"""
vehicle_classes = {
    'passenger': {
        '--vehicle-class': 'passenger',
        '--vclass': 'passenger',
        '--prefix': 'veh',
        '--min-distance': 300,
        '--trip-attributes': 'departLane="best"',
    },
    'bus': {
        '--vehicle-class': 'bus',
        '--vclass': 'bus',
        '--prefix': 'bus',
    },
    'truck': {
        '--vehicle-class': 'truck',
        '--vclass': 'truck',
        '--prefix': 'truck',
        '--min-distance': 600,
        '--trip-attributes': 'departLane="best"',
    }
}


class RandomTripsGenerator:
    def __init__(self, netpath, routepath, output, vclass, density, *flags, **opts):
        self.vclass = vclass
        self.density = density
        self.options = {
            # Default options
            '--net-file': netpath,
            '--output-trip-file': output,
            '--route-file': routepath,
            **opts
        }
        self.flags = [*flags]
        edges = sumolib.net.readNet(netpath).getEdges()
        self._init_trips(edges, vclass, density)
        self.options.update(vehicle_classes[self.vclass])

    def generate(self):
        logging.info(f'Generating trips for vehicle class {self.vclass} with density of {self.density} veh/km/h')
        randomTrips.main(randomTrips.get_options(dict_to_list(self.options) + self.flags))

    def _init_trips(self, edges, vclass, density):
        """
        :param edges: foo.rou.xml
        :param density: vehicle/km/h
        """
        # calculate the total length of the available lanes
        length = 0.
        for edge in edges:
            if edge.allows(vclass):
                length += edge.getLaneNumber() * edge.getLength()

        logging.debug(f'density = {density}')
        period = 3600 / (length / 1000) / density
        logging.debug(f'Period computed for network : {period}, vclass={self.vclass}')
        self.options.update({'-p': period})


class StoreDictKeyPair(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pairs = {}
        for kv in values:
            k, v = kv.split("=")
            pairs[k] = v
        setattr(namespace, self.dest, pairs)


def load_netconvert_template(osm_input, out_name):
    netconfig = ElementTree.parse(os.path.join(TEMPLATEDIR, 'simul.netcfg'))
    root = netconfig.getroot()
    root.find('input/osm-files').set('value', osm_input)
    root.find('output/output-file').set('value', f'{out_name}.net.xml')
    root.find('report/log').set('value', f'{out_name}.netconvert.log')
    return netconfig


def load_polyconvert_template(osm_file, type_file, scenario_name):
    polyconfig = ElementTree.parse(os.path.join(TEMPLATEDIR, 'simul.polycfg'))
    root = polyconfig.getroot()
    root.find('input/osm-files').set('value', osm_file)
    root.find('input/net-file').set('value', f'{scenario_name}.net.xml')
    root.find('input/type-file').set('value', type_file)
    root.find('output/output-file').set('value', f'{scenario_name}.poly.xml')
    root.find('report/log').set('value', f'{scenario_name}.polyconvert.log')
    return polyconfig


def load_sumoconfig_template(simulation_name, routefiles=(), generate_polygons=False, seed=None):
    routefiles = routefiles or (f'{simulation_name}.rou.xml',)
    sumoconfig = ElementTree.parse(os.path.join(TEMPLATEDIR, 'simul.sumocfg'))
    root = sumoconfig.getroot()
    root.find('input/net-file').set('value', f'{simulation_name}.net.xml')
    root.find('input/route-files').set('value', ','.join(routefiles))
    additional = root.find('input/additional-files')
    if generate_polygons:
        additional.set('value', f'{simulation_name}.poly.xml')
    else:
        root.find('input').remove(additional)
    root.find('report/log').set('value', f'{simulation_name}.log')
    # Set the seed for the random number generator. By default, use the current time
    root.find('random_number/seed').set('value', seed or str(time.time()))
    return sumoconfig


def generate_scenario(osm_file, out_path, scenario_name, generate_polygons=False):
    net_template = load_netconvert_template(osm_file, scenario_name)

    with tempfile.TemporaryDirectory() as tmpdirname:
        # Generate NETCONVERT configuration
        netconfig = os.path.join(tmpdirname, f'{scenario_name}.netcfg')
        net_template.write(netconfig)
        # Copy typemaps to tempdir
        shutil.copytree(os.path.join(TEMPLATEDIR, 'typemap'), os.path.join(tmpdirname, 'typemap'))
        # Call NETCONVERT
        logging.info("Generating network…")
        netconvertcmd = [os.path.join(SUMOBIN, 'netconvert'), '-c', netconfig]
        logging.debug(f'Calling {" ".join(netconvertcmd)}')
        subprocess.run(netconvertcmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Optionaly generate polygons
        if generate_polygons:
            generate_polygons_(osm_file, scenario_name, tmpdirname)
        # Move files to destination
        ignore_patterns = shutil.ignore_patterns('*.polycfg', '*.netcfg', 'typemap')
        shutil.copytree(tmpdirname, out_path, ignore=ignore_patterns)


def generate_polygons_(osm_file, scenario_name, dest):
    polyconfig = os.path.join(dest, f'{scenario_name}.polycfg')
    poly_template = load_polyconvert_template(osm_file, 'typemap/osmPolyconvert.typ.xml', scenario_name)
    poly_template.write(polyconfig)
    # Call POLYCONVERT
    logging.info('Generating polygons…')
    polyconvert_cmd = [os.path.join(SUMOBIN, 'polyconvert'), '-c', polyconfig]
    logging.debug(f'Calling {" ".join(polyconvert_cmd)}')
    subprocess.run(polyconvert_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def generate_mobility(out_path, name, vclasses):
    netfile = f'{name}.net.xml'
    netpath = os.path.join(out_path, netfile)
    output = os.path.join(out_path, f'{name}.trips.xml')
    routefiles = []
    end_time = 200
    for vclass, density in vclasses.items():
        # simname.bus.rou.xml, simname.passenger.rou.xml, ...
        routefile = f'{name}.{vclass}.rou.xml'
        routepath = os.path.join(out_path, routefile)
        routefiles.append(routefile)
        logging.debug(routefile)
        generator = RandomTripsGenerator(netpath, routepath, output, vclass, float(density))
        generator.flags.append('-l')
        generator.flags.append('--validate')
        generator.options.update(**{'--end': end_time})
        generator.generate()
    return routefiles


def generate_sumo_configuration(routefiles, path, scenario_name, generate_polygons):
    sumo_template = load_sumoconfig_template(scenario_name, routefiles, generate_polygons)
    sumo_template.write(os.path.join(path, f'{scenario_name}.sumocfg'))


def generate_all(args):
    simulation_name = args.name
    simulation_dir = os.path.join(args.path, simulation_name)
    try:
        generate_polygons = args.generate_polygons
    except AttributeError:
        generate_polygons = False
    osm_file = args.osmfile
    logs_dir = os.path.join(simulation_dir, 'log')

    generate_scenario(osm_file, simulation_dir, simulation_name, generate_polygons)
    routefiles = generate_mobility(simulation_dir, simulation_name, args.vclasses)
    generate_sumo_configuration(routefiles, simulation_dir, simulation_name, generate_polygons)
    # Move all logs to logdir
    move_logs(simulation_dir, logs_dir)


def move_logs(simulation_dir, logs_dir):
    for f in os.listdir(simulation_dir):
        if os.path.splitext(f)[1] == '.log':
            shutil.move(os.path.join(simulation_dir, f), logs_dir)


def dict_to_list(d):
    return [item for k in d for item in (k, d[k])]


def parse_command_line(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('osmfile', help='Path to the .osm file to convert to a SUMO simulation')
    parser.add_argument('--path', help='Where to generate the files')
    parser.add_argument('--name', required=True, help='Name of the SUMO scenario to generate')
    parser.add_argument('--generate-polygons', default=False, action='store_true',
                        help='Whether to generate polygons and POIs (defaults to false).')
    parser.add_argument('--vclass', dest='vclasses', action=StoreDictKeyPair,
                        nargs="+", metavar="VCLASS=DENSITY",
                        help='Generate this vclass with given density, in pair form vclass=density. The density is '
                             'given in vehicles per hour per kilometer. For now, the following vehicle classes are '
                             'available: passenger, truck, bus.')
    parser.add_argument('--seed', help='Initializes the random number generator.')
    return parser.parse_args(args=args)


def handle_args(options):
    # If no vehicle classes are specified, use 'passenger' as a default with a density of 10 cars/km/h.
    options.vclasses = options.vclasses or {'passenger': 10}
    # Delete simul_dir if it already exists
    simul_dir = os.path.join(options.path, options.name)
    if os.path.isdir(simul_dir):
        input(f'{simul_dir} already exists ! Press Enter to delete...')
        shutil.rmtree(simul_dir)
    logging.debug(f'Options : {options}')
    generate_all(options)


def parse_json(json_file):
    logging.info(f'Loading config from {json_file}')
    config = SimpleNamespace(**json.load(json_file))
    logging.debug(f'Config {config}')
    return config


if __name__ == '__main__':
    # Try to load the config file
    if len(argv) > 2 and argv[1] == '-c' or argv[1] == '--config' or argv[1] == '-config':
            try:
                with open(argv[2]) as jsonfile:
                    config = parse_json(jsonfile)
                handle_args(config)
            except FileNotFoundError:
                msg = f'The config file {argv[2]} does not exist!'
                logging.fatal(msg)
                raise FileNotFoundError(msg)
    else:
        # Run with command line arguments
        config = parse_command_line()
        handle_args(config)
