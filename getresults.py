import requests
from bs4 import BeautifulSoup
import re
import os

class FellRunner(object):

    URL = 'http://fellrunner.org.uk/'

    def available_race_years(self):
        """
        () -> Iter[str]

        Returns an iterator of years for which there are results available
        """
        races_url = self.URL + 'races.php'
        response = requests.get(races_url)
        page = response.text
        soup = BeautifulSoup(page, 'lxml')
        pattern = "races.php\\?id=[0-9]*$"
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and re.match(pattern, href):
                _, idx = href.split('=')
                yield idx

    def get_race_year_pages(self, y_idx):
        """
        """
        races_url = self.URL + 'races.php'
        response = requests.get(races_url, params={'y': y_idx})
        page = response.text
        soup = BeautifulSoup(page, 'lxml')
        pattern = "races.php\\?y=%s\\&p=[0-9]*$" % y_idx
        for link in soup.find_all('a'):
            href = link.get('href')
            if not href:
                continue
            href = href.strip('/').replace('&amp;', '&')
            if re.match(pattern, href):
                _, _, page_idx = href.split('=')
                yield page_idx

    def get_race_ids(self, y_idx, p_idx):
        """
        Args:
            y_idx (str): year index, eg '2017'
            p_idx (str): page index, eg '12'

        Returns:
            Iter[str]: iterator of race page ids listed on this page
        """
        races_url = self.URL + 'races.php'
        response = requests.get(races_url, params={'y': y_idx, 'p': p_idx})
        page = response.text
        soup = BeautifulSoup(page, 'lxml')
        pattern = "races.php?id=[0-9]*$"
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and re.match(pattern, href):
                _, race_id = href.split('=')
                yield race_id

    def available_result_years(self):
        """
        () -> Iter[str]

        Returns the list of years for which there are results available
        """
        response = requests.get(self.URL + 'results.php')
        assert response.status_code == 200
        results_page = response.text
        return year_page_idxs(results_page)

    def result_idxs_for_year(self, y_idx):
        """
        (str,) -> Iter[str]

        Returns an iterator of result set indices for the given year
        """
        year_page = self.__get_year_page(y_idx)
        return result_page_idxs(year_page)

    def scrape_csv(self, r_idx):
        page_url = self.URL + 'results.php'
        page = requests.get(page_url, params={'id': r_idx}).text
        soup = BeautifulSoup(page, 'lxml')
        pattern = 'export_results.php\\?format=csv'
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and re.match(pattern, href):
                csv_url = self.URL + href
                csv_response = requests.get(csv_url)
                return csv_response.text

    def __get_year_page(self, year):
        page_url = self.URL + 'results.php'
        results_page = requests.get(page_url, params={'year': year})
        return results_page.text


def result_page_idxs(page):
    soup = BeautifulSoup(page, 'lxml')
    pattern = 'results.php\\?id=[0-9]*$'

    for link in soup.find_all('a'):
        href = link.get('href')
        if href and re.match(pattern, href):
            _, idx = href.split('=')
            yield idx


def year_page_idxs(page):
    soup = BeautifulSoup(page, 'lxml')
    pattern = 'results.php\\?year=[0-9]*$'
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and re.match(pattern, href):
            _, idx = href.split('=')
            yield idx


MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
M_DICT = dict([(m, i + 1) for i, m in enumerate(MONTHS)])


def datestr_to_date(s):
    """ (str,) -> datetime

    Examples:
        >>> datestr_to_date('Sat 3rd Jun 2017 at 15:00')
        (03, 06, 2017)
        >>> datestr_to_date('Sun 12th Jan 2014 at 09:00')
        (12, 01, 2014)
        >>> datestr_to_date('Sat 1st Apr 2017 at 11:00')
        (1, 4, 2017)
    """
    words = s.strip().split()
    day = int(words[1][:-2])
    month = M_DICT[words[2]]
    year = int(words[3])
    return day, month, year


def get_race_info(page):
    soup = BeautifulSoup(page, 'lxml')

    # Race name
    race_header = soup.find('h2', {'class': 'title_races'}).text
    name = race_header.split(u'\u2013')[-1].split('(')[0].strip()

    # Pull info out of the race info table
    raceinfo_ul = soup.find('ul', {'class': 'race_info_list'})
    litems = raceinfo_ul.findAll('li')

    # Date eg: <strong>Date &amp; time:</strong>  Sat 1st Apr 2017 at 11:00
    date_str = litems[0].text.split('time:')[-1].strip()
    date_ints = datestr_to_date(date_str)

    # Distance (km)
    dist_str = litems[4].text.split()[1].strip()
    assert dist_str.endswith('km')
    distance_km = float(dist_str[:-2])

    # Climb (m)
    climb_str = litems[5].text.split()[1].strip()
    assert climb_str.endswith('m')
    climb_m = float(climb_str[:-1])

    return RaceInfo(date=date_ints, name=name,
                    distance_km=distance_km, climb_m=climb_m)


class RaceInfo(object):
    """
    Class to model the data that we want to capture about a specific
    race instance.

    We're capturing all of this info for each year that the race runs
    to give some flexibility for dealing with year-to-year changes in
    the vital statistics.
    """
    def __init__(self, name='', date=None, distance_km=0.0, climb_m=0.0):
        self.name = name
        self.date = date
        self.distance_km = distance_km
        self.climb_m = climb_m


class ResultsFolder(object):
    """
    Class wraps around a folder containing race CSV files
    """
    def __init__(self, folder):
        self.__folder = folder

    def __contains__(self, results_id):
        fpath = os.path.join(self.__folder, results_id + '.csv')
        return os.path.isfile(fpath)

    def add_csv(self, results_id, results_csv):
        fpath = os.path.join(self.__folder, results_id + '.csv')
        with open(fpath, 'w') as f_out:
            f_out.write(results_csv.encode('utf8'))

    def get_resultset(self, results_id):
        """
        Returns the result set for the given race results id

        Returns:
            RaceResultSet
        """
        assert results_id in self
        fpath = os.path.join(self.__folder, results_id + '.csv')
        csv_str = open(fpath, 'r').read()
        return RaceResultSet.from_csv(csv_str)


class RaceResultSet(object):
    """
    Set of results for a race

    Args:
        result_rows (Tuple[str, str, str, int]):
            name, club, category, time (s)
    """
    def __init__(self, result_rows):
        self._result_rows = list(result_rows)

    def __len__(self):
        """
        Number of finishers
        """
        return len(self._result_rows)

    def __getitem__(self, idx):
        return self._result_rows[idx]

    @staticmethod
    def from_csv(csv_str):
        lines = iter(csv_str.split('\n'))
        header = next(lines)
        rows = []
        for lin in lines:
            words = lin.split(',')
            name, club, cat, str_time = words
            seconds = timestr_to_secs(str_time)
            rows.append((name, club, cat, seconds))
        return RaceResultSet(rows)


def timestr_to_secs(str_time):
    """
    str -> int

    Converts a time string to an integer number of seconds

    Examples:
        >>> timestr_to_secs('00:00:30')
        30
        >>> timestr_to_secs('00:10:30')
        630
        >>> timestr_to_secs('01:10:30')
        4230
    """
    components = str_time.split(':')
    hh = int(components[0])
    mm = int(components[1])
    ss = int(components[2])
    return 3600 * hh + 60 * mm + ss


def scrape_race_results():
    folder = 'results'
    res_folder = ResultsFolder(folder)
    fellrunner = FellRunner()
    for y_idx in fellrunner.available_result_years():
        print 'Getting results for year: %s ' % y_idx,
        for r_idx in fellrunner.result_idxs_for_year(y_idx):
            if r_idx in res_folder:
                continue
            race_csv = fellrunner.scrape_csv(r_idx)
            res_folder.add_csv(r_idx, race_csv)
            print '.',


if __name__ == '__main__':
    pass
