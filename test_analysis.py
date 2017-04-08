import unittest
import kcourse.analysis as analysis
import kcourse.file_tools as ft

from os.path import join, dirname, abspath


TEST_PAGES = abspath(join(dirname(__file__), 'test_pages'))


class TestStringMunging(unittest.TestCase):

    def test_timestr_to_secs(self):
        s = '00:55:56'
        expected = 55 * 60 + 56
        returned = ft.timestr_to_secs(s)
        self.assertEquals(expected, returned)

        s = '55:56'
        returned = ft.timestr_to_secs(s)
        self.assertEquals(expected, returned)

        s = u'52\xe2\x80\x9919\xe2\x80\x9d'
        expected = 52 * 60 + 19
        returned = ft.timestr_to_secs(s)
        self.assertEquals(expected, returned)


    def test_munge_line(self):
        s = 'Daniel Miller,Endurance Store,M,00:34:04'
        expected_name = 'daniel miller'
        expected_club = 'endurance store'
        expected_cat = 'm'
        expected_time = 60 * 34 + 4

        name, club, cat, time = analysis.munge_line(s)
        self.assertEquals(expected_name, name)
        self.assertEquals(expected_club, club)
        self.assertEquals(expected_cat, cat)
        self.assertEquals(expected_time, time)

    def test_process_file(self):
        f = join(TEST_PAGES, '100.csv')
        runners = analysis.process_results_file(f)

        self.assertEquals(runners['danny hope'], 48 * 60 + 53)
        self.assertEquals(runners['linda lord'], 3600 + 18 * 60 + 11)

    def test_process_results_collection(self):
        f = join(TEST_PAGES, '100.csv')
        race_data = analysis.process_results_file(f)

        races, runners = analysis.process_results_collection([race_data] * 2)
        self.assertEquals(len(races), 2)
        self.assertEquals(len(runners), len(race_data))

        for r in races:
            for runner_id, time in r.iteritems():
                runner_name = runners[runner_id]
                time2 = race_data[runner_name]
                self.assertEquals(time, time2)

    def test_calc_avg_race_times(self):
        r = {0: 100., 1: 200.}
        expected = 150.
        returned = analysis.calc_avg_race_time(r)
        self.assertEquals(expected, returned)

    def test_ends_2_decimals(self):
        self.assertTrue(analysis.ends_2_decimals('asdf:12'))
        self.assertFalse(analysis.ends_2_decimals('asdf:12a'))

    def test_solver(self):
        runners_actual = [1.0, 2.0]
        races_actual = [1.0, 2.0]

        race_data = [
            {0: 1.0, 1: 2.0},
            {0: 2.0, 1: 4.0}
        ]

        scorer = analysis.Scorer(races=race_data, n_races=2, n_runners=2)
        runners_guess = [1.0, 1.0]
        races_guess = [1.0, 1.0]
        J, race_grads, runner_grads = scorer.cost_function(races_guess, runners_guess)

        expected_J = 5.5
        self.assertEquals(J, expected_J)

        d = races_guess
        h = runners_guess
        grad_d0 = -1.#-h[0] * (1 - )
        self.assertEquals(race_grads[0], grad_d0)

        J, all_grads = scorer.unrolled_cost_function(d + h)
        self.assertEquals(race_grads[0], all_grads[0])