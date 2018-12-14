# -*- coding: utf-8 -*-
import argparse
import os
import shutil
import subprocess
import tempfile
from xml.etree import ElementTree

import sumolib
import randomTrips

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

        period = 3600 / (length / 1000) / density
        print(f'Period computed for network : {period}, vclass={self.vclass}')
        self.flags.extend(['-p', period])


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


def load_sumoconfig_template(simulation_name, routefiles=()):
    routefiles = routefiles or (f'{simulation_name}.rou.xml',)
    sumoconfig = ElementTree.parse(os.path.join(TEMPLATEDIR, 'simul.sumocfg'))
    root = sumoconfig.getroot()
    root.find('input/net-file').set('value', f'{simulation_name}.net.xml')
    root.find('input/route-files').set('value', ','.join(routefiles))
    root.find('input/additional-files').set('value', f'{simulation_name}.poly.xml')
    root.find('report/log').set('value', f'{simulation_name}.log')
    return sumoconfig


def generate_scenario(osm_file, out_path, scenario_name):
    net_template = load_netconvert_template(osm_file, scenario_name)
    poly_template = load_polyconvert_template(osm_file, 'typemap/osmPolyconvert.typ.xml', scenario_name)

    with tempfile.TemporaryDirectory() as tmpdirname:
        # Generate POLYCONVERT and NETCONVERT configuration
        netconfig = os.path.join(tmpdirname, f'{scenario_name}.netcfg')
        polyconfig = os.path.join(tmpdirname, f'{scenario_name}.polycfg')
        net_template.write(netconfig)
        poly_template.write(polyconfig)
        # Copy typemaps to tempdir
        shutil.copytree(os.path.join(TEMPLATEDIR, 'typemap'), os.path.join(tmpdirname, 'typemap'))
        # Call POLYCONVERT and NETCONVERT
        polyconvert_cmd = ['polyconvert', '-c', polyconfig]
        netconvertcmd = ['netconvert', '-c', netconfig]
        subprocess.run(netconvertcmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(polyconvert_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Move files to destination
        ignore_patterns = shutil.ignore_patterns('*.polycfg', '*.netcfg', 'typemap')
        shutil.copytree(tmpdirname, out_path, ignore=ignore_patterns)


def generate_mobility(out_path, name):
    netfile = f'{name}.net.xml'
    netpath = os.path.join(out_path, netfile)
    output = os.path.join(out_path, f'{name}.trips.xml')
    routefiles = []
    end_time = 200
    classes = ('passenger', 'bus')
    for vclass in classes:
        # simname.bus.rou.xml, simname.passenger.rou.xml, ...
        routefile = f'{name}.{vclass}.rou.xml'
        routepath = os.path.join(out_path, routefile)
        routefiles.append(routefile)
        generator = RandomTripsGenerator(netpath, routepath, output, vclass, 10, '-l', **{'--end': end_time})
        generator.generate()
    return routefiles


def generate_sumo_configuration(routefiles, path, scenario_name):
    sumo_template = load_sumoconfig_template(scenario_name, routefiles=routefiles)
    sumo_template.write(os.path.join(path, f'{scenario_name}.sumocfg'))


def generate_all(osm_file, path, simulation_name):
    simulation_dir = os.path.join(path, simulation_name)
    logs_dir = os.path.join(simulation_dir, 'log')
    generate_scenario(osm_file, simulation_dir, simulation_name)
    routefiles = generate_mobility(simulation_dir, simulation_name)
    generate_sumo_configuration(routefiles, simulation_dir, simulation_name)
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
    parser.add_argument('osmfile', type=str)
    parser.add_argument('--path', type=str, help='Where to generate the files')
    parser.add_argument('--name', type=str, required=True, help='Name of the scenario to generate')
    args = parser.parse_args()
    generate_all(args.osmfile, args.path, args.name)


if __name__ == '__main__':
    if os.path.isdir('/tmp/scenario/foo'):
        shutil.rmtree('/tmp/scenario/foo')
    path = '/tmp/scenario/'
    osm = '/tmp/scenario/map.osm'
    generate_all(osm, path, 'foo')
    # main()
