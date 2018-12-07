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
        configurator.generate_scenario(self.sim_path, self.sim_name)
        self.assert_is_dir(self.sim_path)
        self.assert_is_dir(os.path.join(self.sim_path, 'log'))
        generated_files = [
            f'{self.sim_name}.sumocfg',
            f'{self.sim_name}.poly.xml',
            f'{self.sim_name}.net.xml'
        ]
        for f in generated_files:
            self.assert_is_file(os.path.join(self.sim_path, f))

    def test_generate_mobility(self):
        # The scenario must be generated before the mobility
        configurator.generate_scenario(self.sim_path, self.sim_name)
        configurator.generate_mobility(self.sim_path, self.sim_name)
        trips_file = os.path.join(self.sim_path, f'{self.sim_name}.trips.xml')
        self.assert_is_file(trips_file)

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
