import unittest
import tempfile
from os.path import join, exists

from kcourse.file_tools import (process_results_file, read_result_to_race_index,
                                process_results_collection)

from analysis import calc_theta0

TEST_FOLDER = 'test_pages'


class TestParamOrdering(unittest.TestCase):

    def test_run(self):
        idx_file = join(TEST_FOLDER, 'result_to_event_index.dat')
        results_folder = join(TEST_FOLDER, 'results')

        result_to_race, _ = read_result_to_race_index(idx_file)
        print result_to_race
        race_dicts = []
        race_ids = []
        for result_id in result_to_race:
        #for f in os.listdir(folder):
            fpath = join(results_folder, result_id + '.csv')
            if not exists(fpath):
                print 'skipping:',fpath

            race_ids.append(result_id)
            race_data = process_results_file(fpath)
            race_dicts.append(race_data)

        print race_data
        races, runners = process_results_collection(race_dicts)
        race_theta0, runner_theta0 = calc_theta0(races, runners)

        r_theta0_dict = dict(zip(race_ids, race_theta0))
        print runners
        print race_ids
        print race_theta0
        self.assertEquals(r_theta0_dict['111'], 1.0)
        self.assertEquals(r_theta0_dict['222'], 2.0)
        self.assertEquals(r_theta0_dict['333'], 3.0)

        f = 'asdf.txt'
        