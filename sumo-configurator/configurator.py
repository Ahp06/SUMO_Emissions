# -*- coding: utf-8 -*-
import os
import shutil
import subprocess

import randomTrips

SIMNAME = 'simul'
NETCONVERTCMD = ['netconvert', '-c', f'static/{SIMNAME}.netcfg']
POLYCONVERTCMD = ['polyconvert', '-c', f'static/{SIMNAME}.polycfg']


def clean():
    # [os.remove(os.path.join('simul', f)) for f in os.listdir('simul')]
    [os.remove(os.path.join('static', f))
     for f in os.listdir('static') if f.endswith('.log')]


def generate_scenario(out_path, name):
    print('Creating the network…')
    subprocess.run(NETCONVERTCMD)
    print('Extracting polygons…')
    subprocess.run(POLYCONVERTCMD)
    print('Moving files')
    shutil.move('static/simul.net.xml', os.path.join(out_path, f'{name}.net.xml'))
    shutil.move('static/simul.poly.xml', os.path.join(out_path, f'{name}.poly.xml'))
    shutil.copyfile('static/simul.sumocfg', os.path.join(out_path, f'{name}.sumocfg'))
    # Move log files
    logdir = os.path.join(out_path, 'log')
    os.mkdir(logdir)
    for f in os.listdir('static'):
        if f.endswith('.log'):
            shutil.move(os.path.join('static', f), os.path.join(logdir, f))


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


def generate_all(output_path, simulation_name):
    output_path = os.path.join(output_path, simulation_name)
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    generate_scenario(output_path, simulation_name)
    generate_mobility(output_path, simulation_name)


if __name__ == '__main__':
    clean()
    generate_all('/tmp/', 'simul')
