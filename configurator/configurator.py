# -*- coding: utf-8 -*-
import os
import shutil
import subprocess
import tempfile
from xml.etree import ElementTree

import randomTrips

# Absolute path of the directory the script is in
SCRIPTDIR = os.path.dirname(__file__)
TEMPLATEDIR = os.path.join(SCRIPTDIR, 'templates')

vehicle_classes = {
    'passenger': {
        '--vehicle-class': 'passenger',
        '--vclass': 'passenger',
        '--prefix': 'veh'
    },
    'bus': {
        '--vehicle-class': 'bus',
        '--vclass': 'bus',
        '--prefix': 'bus'
    }
}


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
    for veh_class in classes:
        # simname.bus.rou.xml, simname.passenger.rou.xml, ...
        routefile = f'{name}.{veh_class}.rou.xml'
        routepath = os.path.join(out_path, routefile)
        routefiles.append(routefile)
        options = {
            '--net-file': netpath,
            '--output-trip-file': output,
            '--route-file': routepath,
            '-e': end_time
        }
        options.update(vehicle_classes[veh_class])
        flags = ['-l']
        generate_random_trips(flags, options)
    return routefiles


def generate_random_trips(flags, options):
    randomTrips.main(randomTrips.get_options(dict_to_list(options) + flags))


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


if __name__ == '__main__':
    if os.path.isdir('/tmp/scenario/foo'):
        shutil.rmtree('/tmp/scenario/foo')
    path = '/tmp/scenario/'
    osm = '/tmp/scenario/map.osm'
    generate_all(osm, path, 'foo')
