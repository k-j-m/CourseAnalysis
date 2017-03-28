import unittest
from os.path import join, dirname, abspath

from getresults import get_race_info

TEST_PAGES = abspath(join(dirname(__file__), 'test_pages'))


class TestRaceInfoPage(unittest.TestCase):
    """
    All tests relating to a specific race instance page.
    """

    def setUp(self):
        self.page = open(join(TEST_PAGES, 'chickenrun2017.html')).read()

    def test_get_date(self):
        """
        Retrieve RaceInfo object from the page and check the date
        """
        expected_date = (1, 4, 2017)
        rinfo = get_race_info(self.page)
        returned_date = rinfo.date
        self.assertEquals(expected_date, returned_date)

    def test_get_name(self):
        """
        Retrieve RaceInfo object and check the name
        """
        expected_name = 'Chicken Run'
        rinfo = get_race_info(self.page)
        returned_name = rinfo.name
        self.assertEquals(expected_name, returned_name)

    def test_get_distance(self):
        """
        Make sure that we can read the distance of a race
        """
        expected_dist = 9.4
        rinfo = get_race_info(self.page)
        returned_dist = rinfo.distance_km
        self.assertEquals(expected_dist, returned_dist)

    def test_get_climb(self):
        """
        Read the climb
        """
        expected_climb = 322.0
        rinfo = get_race_info(self.page)
        returned_climb = rinfo.climb_m
        self.assertEquals(expected_climb, returned_climb)


class TestCornercases(unittest.TestCase):
    """
    Throw in some corner cases to make sure the thing behaves
    as expected.
    """

    #page = open(join(TEST_))


if __name__ == '__main__':
    unittest.main()
