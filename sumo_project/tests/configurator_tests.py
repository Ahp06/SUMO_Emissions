import os
import shutil
import tempfile
import unittest

import configurator

# Absolute path of the directory the script is in
SCRIPTDIR = os.path.dirname(__file__)


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.sim_name = 'test_simulation'
        self.sim_path = '/test_simulation'
        self.log_path = '/test_simulation/log'

    def test_load_netconvert_template(self):
        tree = configurator.load_netconvert_template('test.osm', 'test_simulation')
        self.assertEqual(tree.find('input/osm-files').get('value'), 'test.osm')
        self.assertEqual(tree.find('output/output-file').get('value'), f'{self.sim_name}.net.xml')
        self.assertEqual(tree.find('report/log').get('value'), f'{self.sim_name}.netconvert.log')

    def test_load_sumoconfig_template_default(self):
        tree = configurator.load_sumoconfig_template(self.sim_name)
        self.assertEqual(tree.find('input/net-file').get('value'), f'{self.sim_name}.net.xml')
        self.assertEqual(tree.find('input/route-files').get('value'), f'{self.sim_name}.rou.xml')
        self.assertEqual(tree.find('report/log').get('value'), f'{self.sim_name}.log')

    def test_load_sumoconfig_template_with_polygons(self):
        tree = configurator.load_sumoconfig_template(self.sim_name, generate_polygons=True)
        self.assertEqual(tree.find('input/net-file').get('value'), f'{self.sim_name}.net.xml')
        self.assertEqual(tree.find('input/route-files').get('value'), f'{self.sim_name}.rou.xml')
        self.assertEqual(tree.find('report/log').get('value'), f'{self.sim_name}.log')
        self.assertEqual(tree.find('input/additional-files').get('value'), f'{self.sim_name}.poly.xml')

    def test_load_sumoconfig_template_with_routefiles(self):
        routefiles = (f'{self.sim_name}.bus.rou.xml', f'{self.sim_name}.passenger.rou.xml')
        tree = configurator.load_sumoconfig_template(self.sim_name, routefiles)
        self.assertEqual(tree.find('input/net-file').get('value'), f'{self.sim_name}.net.xml')
        self.assertEqual(tree.find('input/route-files').get('value'), ','.join(routefiles))
        self.assertEqual(tree.find('report/log').get('value'), f'{self.sim_name}.log')

    def test_load_polyconvert_template(self):
        tree = configurator.load_polyconvert_template(
            osm_file=f'{self.sim_name}.osm',
            type_file='typemap/test.typ.xml',
            scenario_name=f'{self.sim_name}'
        )
        self.assertEqual(tree.find('input/osm-files').get('value'), f'{self.sim_name}.osm')
        self.assertEqual(tree.find('input/net-file').get('value'), f'{self.sim_name}.net.xml')
        self.assertEqual(tree.find('input/type-file').get('value'), 'typemap/test.typ.xml')
        self.assertEqual(tree.find('output/output-file').get('value'), f'{self.sim_name}.poly.xml')
        self.assertEqual(tree.find('report/log').get('value'), f'{self.sim_name}.polyconvert.log')


class GenerationTests(unittest.TestCase):

    def setUp(self):
        self.base_path = tempfile.mkdtemp()
        self.sim_name = 'test_simulation'
        self.sim_path = os.path.join(self.base_path, self.sim_name)
        self.log_path = os.path.join(self.sim_name, 'log')

    def tearDown(self):
        shutil.rmtree(self.base_path)

    def test_generate_scenario(self):
        osm_file = os.path.join(SCRIPTDIR, 'sample.osm')
        configurator.generate_scenario(osm_file, self.sim_path, self.sim_name, generate_polygons=False)
        self.assert_is_file(os.path.join(self.sim_path, f'{self.sim_name}.net.xml'))

    def test_generate_scenario_with_polygons(self):
        osm_file = os.path.join(SCRIPTDIR, 'sample.osm')
        configurator.generate_scenario(osm_file, self.sim_path, self.sim_name, generate_polygons=True)
        self.assert_is_dir(self.sim_path)
        generated_files = [
            f'{self.sim_name}.poly.xml',
            f'{self.sim_name}.net.xml'
        ]
        for f in generated_files:
            self.assert_is_file(os.path.join(self.sim_path, f))

    def test_generate_mobility(self):
        # The scenario must be generated before the mobility
        osm_file = os.path.join(SCRIPTDIR, 'sample.osm')
        trips_file = os.path.join(self.sim_path, f'{self.sim_name}.trips.xml')
        configurator.generate_scenario(osm_file, self.sim_path, self.sim_name)
        classes = {'passenger': 10, 'truck': 1}
        routefiles = configurator.generate_mobility(self.sim_path, self.sim_name, vclasses=classes)

        self.assert_is_file(trips_file)
        for f in routefiles:
            self.assert_is_file(os.path.join(self.sim_path, f))

    def assert_exists(self, path):
        self.assertTrue(os.path.exists(path), msg=f'{path} does not exist')

    def assert_is_file(self, path):
        self.assert_exists(path)
        self.assertTrue(os.path.isfile(path), msg=f'{path} is not a file')

    def assert_is_dir(self, path):
        self.assert_exists(path)
        self.assertTrue(os.path.isdir(path), msg=f'{path} is not a directory')


if __name__ == '__main__':
    unittest.main()
