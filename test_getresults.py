import unittest
from os.path import join, dirname, abspath

from getresults import get_race_info, BadRaceInfo, get_available_race_years

TEST_PAGES = abspath(join(dirname(__file__), 'test_pages'))


class TestRaceInfoYears(unittest.TestCase):

    def setUp(self):
        self.page = open(join(TEST_PAGES, 'chickenrun2017.html')).read()

    def test_get_years(self):
        expected_years = set(['2010','2011','2012','2013',
                              '2014','2015','2016','2017'])
        returned_years = set(get_available_race_years(self.page))
        self.assertEquals(expected_years, returned_years)


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

    def test_nav_course(self):
        """
        The FRA nav course isn't a race and so should complain when
        we try to get its info.
        """
        page = open(join(TEST_PAGES, 'nav_course.html'))
        self.assertRaises(BadRaceInfo, get_race_info, page)

    def test_bad_page(self):
        """
        Something wrong with 2017 wardle skyline... don't know what
        """
        page = open(join(TEST_PAGES, 'race_5214.html'))
        rinfo = get_race_info(page)


if __name__ == '__main__':
    unittest.main()
