# -*- coding: utf-8 -*-
import argparse
import os
import shutil
import subprocess
import tempfile
from xml.etree import ElementTree

import randomTrips
import sumolib

# Absolute path of the directory the script is in
SCRIPTDIR = os.path.dirname(__file__)
TEMPLATEDIR = os.path.join(SCRIPTDIR, 'templates')

vehicle_classes = {
    'passenger': {
        '--vehicle-class': 'passenger',
        '--vclass': 'passenger',
        '--prefix': 'veh',
        '--min-distance': 300,
        '--trip-attributes': 'departLane="best"',
        # '--validate': True
    },
    'bus': {
        '--vehicle-class': 'bus',
        '--vclass': 'bus',
        '--prefix': 'bus',
        # '--validate': True
    },
    'truck': {
        '--vehicle-class': 'truck',
        '--vclass': 'truck',
        '--prefix': 'truck',
        '--min-distance': 600,
        '--trip-attributes': 'departLane="best"',
        # '--validate': True
    }
}


class RandomTripsGenerator:
    def __init__(self, netpath, routepath, output, vclass, density, *flags, **opts):
        self.vclass = vclass
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

    def add_option(self, opt_name, value):
        self.options[opt_name] = value

    def generate(self):
        print(f'Generating trips for vehicle class {self.vclass}')
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

        print(f'density = {density}')
        period = 3600 / (length / 1000) / density
        print(f'Period computed for network : {period}, vclass={self.vclass}')
        self.flags.extend(['-p', period])


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


def load_sumoconfig_template(simulation_name, routefiles=(), generate_polygons=False):
    routefiles = routefiles or (f'{simulation_name}.rou.xml',)
    sumoconfig = ElementTree.parse(os.path.join(TEMPLATEDIR, 'simul.sumocfg'))
    root = sumoconfig.getroot()
    root.find('input/net-file').set('value', f'{simulation_name}.net.xml')
    root.find('input/route-files').set('value', ','.join(routefiles))
    if generate_polygons:
        root.find('input/additional-files').set('value', f'{simulation_name}.poly.xml')
    root.find('report/log').set('value', f'{simulation_name}.log')
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
        print("Generate network...")
        netconvertcmd = ['netconvert', '-c', netconfig]
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
    print('Generate polygons...')
    polyconvert_cmd = ['polyconvert', '-c', polyconfig]
    subprocess.run(polyconvert_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def generate_mobility(out_path, name, vclasses):
    netfile = f'{name}.net.xml'
    netpath = os.path.join(out_path, netfile)
    output = os.path.join(out_path, f'{name}.trips.xml')
    routefiles = []
    end_time = 200
    for vclass in vclasses:
        # simname.bus.rou.xml, simname.passenger.rou.xml, ...
        routefile = f'{name}.{vclass}.rou.xml'
        routepath = os.path.join(out_path, routefile)
        routefiles.append(routefile)
        generator = RandomTripsGenerator(netpath, routepath, output, vclass, 10.0, '-l', **{'--end': end_time})
        generator.generate()
    return routefiles


def generate_sumo_configuration(routefiles, path, scenario_name, generate_polygons=False):
    sumo_template = load_sumoconfig_template(scenario_name, routefiles=routefiles, generate_polygons=False)
    sumo_template.write(os.path.join(path, f'{scenario_name}.sumocfg'))


def generate_all(args):
    simulation_name = args.name
    simulation_dir = os.path.join(args.path, simulation_name)
    osm_file = args.osmfile
    logs_dir = os.path.join(simulation_dir, 'log')
    generate_scenario(osm_file, simulation_dir, simulation_name, args.generate_polygons)
    routefiles = generate_mobility(simulation_dir, simulation_name, args.vclasses)
    generate_sumo_configuration(routefiles, simulation_dir, simulation_name, args.generate_polygons)
    # Move all logs to logdir
    move_logs(simulation_dir, logs_dir)


def move_logs(simulation_dir, logs_dir):
    for f in os.listdir(simulation_dir):
        if os.path.splitext(f)[1] == '.log':
            shutil.move(os.path.join(simulation_dir, f), logs_dir)


def dict_to_list(d):
    return [item for k in d for item in (k, d[k])]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('osmfile', help='Path to the .osm file to convert to a SUMO simulation')
    parser.add_argument('--path', help='Where to generate the files')
    parser.add_argument('--name', required=True, help='Name of the SUMO scenario to generate')
    parser.add_argument('--generate-polygons', default=False)
    parser.add_argument('--vclass', dest='vclasses', action=StoreDictKeyPair,
                        nargs="+", metavar="VCLASS=DENSITY",
                        help='Generate this vclass with given density, in pair form vclass=density. The density is '
                             'given in vehicles per hour per kilometer.')
    options = parser.parse_args()
    # If no vehicle classes are specified, use 'passenger' as a default
    vclasses = options.vclasses or ('passenger',)
    # FIXME Delete simul_dir if it already exists
    simul_dir = os.path.join(options.path, options.name)
    if os.path.isdir(simul_dir):
        input(f'{simul_dir} already exists ! Press Enter to overwrite...')
        shutil.rmtree(simul_dir)
    generate_all(options)


if __name__ == '__main__':
    main()
