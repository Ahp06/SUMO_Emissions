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


def load_netconvert_template(osm_input, out_name):
    tree = ElementTree.parse(os.path.join(TEMPLATEDIR, 'simul.netcfg'))
    root = tree.getroot()
    root.find('input/osm-files').set('value', osm_input)
    root.find('output/output-file').set('value', f'{out_name}.net.xml')
    root.find('report/log').set('value', f'{out_name}.netconvert.log')
    return tree


def load_polyconvert_template(osm_file, type_file, scenario_name):
    tree = ElementTree.parse(os.path.join(TEMPLATEDIR, 'simul.polycfg'))
    root = tree.getroot()
    root.find('input/osm-files').set('value', osm_file)
    root.find('input/net-file').set('value', f'{scenario_name}.net.xml')
    root.find('input/type-file').set('value', type_file)
    root.find('output/output-file').set('value', f'{scenario_name}.poly.xml')
    root.find('report/log').set('value', f'{scenario_name}.polyconvert.log')
    return tree


def load_sumoconfig_template(simulation_name):
    tree = ElementTree.parse(os.path.join(TEMPLATEDIR, 'simul.sumocfg'))
    root = tree.getroot()
    root.find('input/net-file').set('value', f'{simulation_name}.net.xml')
    root.find('input/route-files').set('value', f'{simulation_name}.rou.xml')
    root.find('input/additional-files').set('value', f'{simulation_name}.poly.xml')
    root.find('report/log').set('value', f'{simulation_name}.log')
    return tree


def generate_scenario(osm_file, out_path, scenario_name):
    net_template = load_netconvert_template(osm_file, scenario_name)
    poly_template = load_polyconvert_template(osm_file, 'typemap/osmPolyconvert.typ.xml', scenario_name)

    with tempfile.TemporaryDirectory() as tmpdirname:
        netconfig = os.path.join(tmpdirname, f'{scenario_name}.netcfg')
        polyconfig = os.path.join(tmpdirname, f'{scenario_name}.polycfg')
        net_template.write(netconfig)
        poly_template.write(polyconfig)
        # Copy typemaps to tempdir
        shutil.copytree(os.path.join(TEMPLATEDIR, 'typemap'), os.path.join(tmpdirname, 'typemap'))
        polyconvert_cmd = ['polyconvert', '-c', polyconfig]
        netconvertcmd = ['netconvert', '-c', netconfig]
        subprocess.run(netconvertcmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(polyconvert_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Move files to destination
        for f in os.listdir(tmpdirname):
            if f.endswith('netcfg') or f.endswith('polycfg') or f == 'typemap':
                continue
            shutil.move(os.path.join(tmpdirname, f), os.path.join(out_path, f))


def generate_mobility(path, name):
    routefile = os.path.join(path, f'{name}.rou.xml')
    netfile = os.path.join(path, f'{name}.net.xml')
    output = os.path.join(path, f'{name}.trips.xml')
    end_time = 200
    veh_class = 'passenger'
    options = [
        f'--net-file={netfile}',
        f'--route-file={routefile}',
        f'--end={end_time}',
        f'--vehicle-class={veh_class}',
        f'--output-trip-file={output}',
        '--validate',
        '--length',
    ]
    print('Generating mobility…')
    randomTrips.main(randomTrips.get_options(options))


def generate_sumo_configuration(path, scenario_name):
    sumo_template = load_sumoconfig_template(scenario_name)
    sumo_template.write(os.path.join(path, f'{scenario_name}.sumocfg'))


def generate_all(osm_file, output_path, simulation_name):
    simulation_dir = os.path.join(output_path, simulation_name)
    logs_dir = os.path.join(simulation_dir, 'log')
    if not os.path.exists(simulation_dir):
        os.mkdir(simulation_dir)
        os.mkdir(logs_dir)
    generate_scenario(osm_file, simulation_dir, simulation_name)
    generate_mobility(simulation_dir, simulation_name)
    generate_sumo_configuration(simulation_dir, simulation_name)
    # Move all logs to logdir
    move_logs(simulation_dir, logs_dir)


def move_logs(simulation_dir, logs_dir):
    for f in os.listdir(simulation_dir):
        if os.path.splitext(f)[1] == '.log':
            shutil.move(os.path.join(simulation_dir, f), logs_dir)


if __name__ == '__main__':
    if os.path.isdir('/tmp/scenario/foo'):
        shutil.rmtree('/tmp/scenario/foo')
    path = '/tmp/scenario/'
    osm = '/tmp/scenario/map.osm'
    generate_all(osm, path, 'foo')
