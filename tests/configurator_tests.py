import os
import shutil
import tempfile
import unittest
from configurator import configurator


class ConfiguratorTests(unittest.TestCase):

    def setUp(self):
        self.sim_path = tempfile.mkdtemp()
        self.sim_name = 'test_simulation'

    def tearDown(self):
        shutil.rmtree(self.sim_path)

    def test_generate_scenario(self):
        osm_file = os.path.abspath('sample.osm')
        configurator.generate_scenario(osm_file, self.sim_path, self.sim_name)
        self.assert_is_dir(self.sim_path)
        # self.assert_is_dir(os.path.join(self.sim_path, 'log'))
        generated_files = [
            f'{self.sim_name}.poly.xml',
            f'{self.sim_name}.net.xml'
        ]
        for f in generated_files:
            self.assert_is_file(os.path.join(self.sim_path, f))

    def test_generate_mobility(self):
        # The scenario must be generated before the mobility
        osm_file = os.path.abspath('sample.osm')
        configurator.generate_scenario(osm_file, self.sim_path, self.sim_name)
        configurator.generate_mobility(self.sim_path, self.sim_name)
        trips_file = os.path.join(self.sim_path, f'{self.sim_name}.trips.xml')
        self.assert_is_file(trips_file)

    def test_load_netconvert_template(self):
        tree = configurator.load_netconvert_template('test.osm', 'test_simulation')
        self.assertEqual(tree.find('input/osm-files').get('value'), 'test.osm')
        self.assertEqual(tree.find('output/output-file').get('value'), f'{self.sim_name}.net.xml')
        self.assertEqual(tree.find('report/log').get('value'), f'{self.sim_name}.netconvert.log')

    def test_load_sumoconfig_template(self):
        tree = configurator.load_sumoconfig_template(self.sim_name)
        self.assertEqual(tree.find('input/net-file').get('value'), f'{self.sim_name}.net.xml')
        self.assertEqual(tree.find('input/route-files').get('value'), f'{self.sim_name}.rou.xml')
        self.assertEqual(tree.find('input/additional-files').get('value'), f'{self.sim_name}.poly.xml')
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