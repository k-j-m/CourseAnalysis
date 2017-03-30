import unittest
from os.path import join, dirname, abspath

from getresults import (get_race_info, BadRaceInfo, get_available_race_years,
                        result_table_entries_from_page, race_ids_from_race_table_page,
                        normalise_name)

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


class TestCornerCases(unittest.TestCase):
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

    def test_slieve_donard(self):
        """
        For whatever reason Slieve Donard isn't picked up from the 2016 races...
        """
        # first make sure that we find it in the race table
        page = open(join(TEST_PAGES, '2016_races_p2.html'))
        race_ids = set(race_ids_from_race_table_page(page))
        self.assertTrue('4212' in  race_ids)

        # then make sure we can get the race info
        page = open(join(TEST_PAGES, '2016_slieve_donard.html'))
        race_info = get_race_info(page)

    def test_intermediate_normalise(self):
        s = 'Andrew Heywood Memorial Windgather'
        expected = 'windgather'
        returned = normalise_name(s)
        self.assertEquals(expected, returned)

        s = 'david bell memorial - seniors'
        expected = 'david bell'
        returned = normalise_name(s)
        self.assertEquals(expected, returned)


class TestRaceResultTable(unittest.TestCase):
    """
    Tests the code that builds a local index of race results
    """

    def test_result_table_entries_from_page(self):
        page = open(join(TEST_PAGES, '2016_results.html'))
        entries = list(result_table_entries_from_page(page))


if __name__ == '__main__':
    unittest.main()
