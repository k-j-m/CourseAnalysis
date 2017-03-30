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
        return get_available_race_years(page)

    def result_table_entries(self, y_idx):
        """ (str) -> Iter[Tuple[str, str, str]]
        result_id, name, date
        """
        results_url = self.URL + 'results.php'
        response = requests.get(results_url, {'year': y_idx})
        page = response.text
        return result_table_entries_from_page(page)

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
        return race_ids_from_race_table_page(page)

    def get_race_info(self, r_idx):
        """ (str,) -> RaceInfo

        Returns the race information for the given race index
        """
        races_url = self.URL + 'races.php'
        response = requests.get(races_url, {'id': r_idx})
        assert response.status_code == 200
        page = response.text
        return get_race_info(page)

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


def get_available_race_years(page):
    soup = BeautifulSoup(page, 'lxml')
    pattern = "races.php\\?y=[0-9]*$"
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and re.match(pattern, href):
            _, idx = href.split('=')
            yield idx


MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
M_DICT = dict([(m, i + 1) for i, m in enumerate(MONTHS)])


def race_ids_from_race_table_page(page):
    soup = BeautifulSoup(page, 'lxml')
    pattern = "races.php\\?id=[0-9]*$"
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and re.match(pattern, href):
            _, race_id = href.split('=')
            yield race_id


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


def _is_valid_category(s):
    """ (str,) -> bool
    >>> _is_valid_category('AL')
    True
    >>> _is_valid_category('Unknown')
    False
    """
    if len(s) != 2:
        return False

    if s[0] not in ['A', 'B', 'C']:
        return False

    if s[1] not in ['S', 'M', 'L']:
        return False

    return True


def get_race_info(page):
    soup = BeautifulSoup(page, 'lxml')

    # Pull info out of the race info table
    raceinfo_ul = soup.find('ul', {'class': 'race_info_list'})
    litems = raceinfo_ul.findAll('li')

    indexed_litems = {}
    for litem in litems:
        words = litem.text.split(':')
        if len(words) <= 1:
            continue
        keyword = str(words[0])
        indexed_litems[keyword] = litem.text

    category = indexed_litems['Category'].split()[1].strip()
    if not _is_valid_category(category):
        raise BadRaceInfo

    # Race name
    race_header = soup.find('h2', {'class': 'title_races'}).text
    name = race_header.split(u'\u2013')[-1].split('(')[0].strip()
    name = name.lower()
    name = name.replace("'", "")

    # Date eg: <strong>Date &amp; time:</strong>  Sat 1st Apr 2017 at 11:00
    date_str = indexed_litems['Date & time'].split('time:')[-1].strip()
    date_ints = datestr_to_date(date_str)

    # Distance (km)
    dist_str = indexed_litems['Distance'].split()[1].strip()
    if dist_str == 'Unknown':
        raise BadRaceInfo

    assert dist_str.endswith('km'), dist_str
    distance_km = float(dist_str[:-2])

    # Climb (m)
    climb_str = indexed_litems['Climb'].split()[1].strip()
    assert climb_str.endswith('m')
    climb_m = float(climb_str[:-1])

    return RaceInfo(date=date_ints, name=name,
                    distance_km=distance_km, climb_m=climb_m)


def result_table_entries_from_page(page):
    """
    Given a results page this yields successive entries of
    (result_id, race_name, race_date)
    """
    pattern = 'results.php\\?id=[0-9]*$'
    soup = BeautifulSoup(page, 'lxml')
    table = soup.find('table', {'id': 'posts-table'})
    if table is None:
        return

    rows = table.find("tbody").find_all("tr")
    for row in rows:
        tds = row.find_all('td')
        date_str = tds[0].text
        date_str.replace('-', '/')
        date = map(int, date_str.split('/'))

        name = tds[1].text
        name = name.lower()
        name.replace("'", "")

        link = tds[2].find('a')
        if link:
            href = link.get('href')
            href = href.split('/')[-1]

            if re.match(pattern, href):
                result_id = href.split('=')[-1]
                yield result_id, name, date


class BadRaceInfo(ValueError):
    pass


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

    def to_json(self):
        return {
            'name': self.name,
            'date': self.date,
            'distance_km': self.distance_km,
            'climb_m': self.climb_m,
        }


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


class RaceInfoTable(object):

    def __init__(self, f):
        if not os.path.exists(f):
            with open(f, 'w') as f_out:
                f_out.write('index\tname\tdate\tdistance_km\tclimb_m\n')
        self._f = f

        self._indices = set()
        with open(f) as f_in:
            next(f_in) # throw away header
            for line in f_in:
                idx = line.split()[0]
                self._indices.add(idx)

    def __contains__(self, idx):
        return idx in self._indices

    def add(self, idx, race_info):
        with open(self._f, 'a') as f_a:
            date_str = '-'.join(map(str, race_info.date))
            f_a.write('%s\t%s\t%s\t%s\t%s\n' % (idx, race_info.name.encode('utf8'), date_str,
                                                race_info.distance_km, race_info.climb_m))

    def __iter__(self):
        with open(self._f, 'r') as f_in:
            next(f_in)
            for line in f_in:
                idx, name, datestr, dist_km, climb_m = line.strip().split('\t')
                yield idx, name, datestr, dist_km, climb_m


class ResultTable(object):
    def __init__(self, f):
        if not os.path.exists(f):
            with open(f, 'w') as f_out:
                f_out.write('result_index\tname\tdate\n')
        self._f = f

        self._result_ids = {}
        with open(f) as f_in:
            next(f_in)
            for line in f_in:
                result_id, name, date_str = line.strip().split('\t')
                date = tuple(map(int, date_str.split('-')))

                entry = result_id, name, date_str
                self._result_ids[result_id] = entry

    def __contains__(self, result_index):
        return result_index in self._result_ids

    def add(self, result_index, name, date):
        if result_index in self:
            return None

        with open(self._f, 'a') as f_out:
            date_str = '-'.join(map(str, date))
            f_out.write('%s\t%s\t%s\n' % (result_index, name.encode('utf8'), date_str))

    def __iter__(self):
        return iter(self._result_ids.values())


def build_race_info_table():
    """
    Builds a local database of race information.

    This includes name, date, distance and climb.
    """
    rinfo_table = RaceInfoTable('rinfo.dat')

    fellrunner = FellRunner()

    y_idxs = fellrunner.available_race_years()
    for y_idx in y_idxs:
        print 'Year %s\t' % y_idx,
        p_idxs = fellrunner.get_race_year_pages(y_idx)
        for p_idx in p_idxs:
            print p_idx,
            r_idxs = fellrunner.get_race_ids(y_idx, p_idx)
            for r_idx in r_idxs:
                print '.',
                if r_idx in rinfo_table:
                    continue
                try:
                    rinfo = fellrunner.get_race_info(r_idx)
                except BadRaceInfo:
                    pass
                except Exception:
                    with open('error.log', 'a') as f_out:
                        f_out.write('Error for race id: %s\n' % r_idx)
                else:
                    rinfo_table.add(r_idx, rinfo)
        print ''


def build_results_table():
    """
    Builds a local table of race name, date and results ID
    for a race.
    """
    result_table = ResultTable('resulttable.dat')
    fellrunner = FellRunner()

    # TODO: iterate through fellrunner yearly result pages and
    #     build our local index of race results in a csv file
    y_idxs = fellrunner.available_result_years()
    for y_idx in ['2009']:#y_idxs:
        print 'Getting results for year:', y_idx
        for result_idx, name, date in fellrunner.result_table_entries(y_idx):
            result_table.add(result_idx, name, date)


def build_result_to_race_index():
    rinfo_names = {}
    with open('rinfo_norm.dat') as f_norm_rinfo:
        next(f_norm_rinfo)
        for line in f_norm_rinfo:
            words = line.strip().split('\t')
            idx = words[0]
            name = words[1]
            rinfo_names[idx] = name

    result_names = {}
    with open('results_norm.dat') as f_norm_res:
        next(f_norm_res)
        for line in f_norm_res:
            words = line.strip().split('\t')
            idx = words[0]
            name = words[1]
            result_names[idx] = name

    result_table = ResultTable('resulttable.dat')
    race_table = RaceInfoTable('rinfo.dat')

    seen_already = set()
    double_ups = []
    races = {}
    for idx, name, datestr, dist_km, climb_m in race_table:
        name = rinfo_names[idx]
        if (name, datestr) in seen_already:
            if (name, datestr) in races:
                del races[(name, datestr)]
            double_ups.append((idx, name, datestr))
        else:
            seen_already.add((name, datestr))
            races[(name, datestr)] = idx

    if double_ups:
        with open('ambiguous_races.log', 'w') as dbl_log:
            for words in double_ups:
                dbl_log.write('\t'.join(words) + '\n')
        # raise Exception('Name normalising is too liberal, see ambiguous_races.log for info')

    miss_count = 0
    hit_count = 0
    with open('orphan_results.log', 'w') as log:
        with open('result_to_race_index.dat', 'w') as idx_file:
            idx_file.write('result_id\trace_id\n')

            for result_id, name, datestr in result_table:
                norm_name = result_names[result_id]
                if result_id == '345':
                    print norm_name, datestr
                if (norm_name, datestr) in races:
                    hit_count += 1
                    race_id = races[(norm_name, datestr)]
                    idx_file.write('%s\t%s\n' % (result_id, race_id))
                else:
                    miss_count += 1
                    log.write('%s\t%s\t%s\n' % (result_id, name, datestr))

    return 1.0 * hit_count / (hit_count + miss_count)


def normalise_name(s):
    # default pass-through: 0.58023
    # convert to lower case: 0.5932
    # drop 'race' as last word: 0.6028
    # drop 'hill' as last word: 0.6037
    # drop initial 'isle of': 0.6041
    # drop final 'memorial': 0.60494
    # drop leading ordinals: 0.60787
    # drop trailing 'reverse': 0.6083
    # drop trailing 'valleys': 0.6087
    # remove hyphens '-' and drop trailing 'seniors': 0.6305
    #     and trailing 'senior': 0.6339
    #     and trailing 'men' and 'mens': 0.64013
    # special case for 'chevin' races: 0.6426
    # use only what follows intermediate 'memorial': 0.648093
    # drop leading ras (welsh for race, I guess): 0.6489
    # drop trailing 'valley': 0.64935
    # drop trailing 'run': 0.6502
    s = s.lower()
    words = s.split()
    if words[0] == 'ras':
        words = words[1:]
    if words[-1] == 'reverse':
        words = words[:-1]
    if words[-1] == 'race' or words[-1] == 'run':
        words = words[:-1]
    if words[-1] == 'hill':
        words = words[:-1]
    if (len(words) > 2) and (words[0] + words[1] == 'isleof'):
        words = words[2:]
    if words[-1] == 'valleys' or words[-1] == 'valley':
        words = words[:-1]

    words = [w for w in words if w != '-']
    if words[-1] == 'seniors':
        words = words[:-1]
    if words[-1] == 'senior':
        words = words[:-1]
    if words[-1] == 'men' or words[-1] == 'mens':
        words = words[:-1]

    if words[-1] == 'memorial':
        words = words[:-1]

    try:
        idx = words.index('memorial')
        words = words[idx + 1:]
    except:
        pass

    ordinal_pattern = '.[0-9](st|nd|rd|th)'
    if not words:
        print s
    if re.match(ordinal_pattern, words[0]):
        words = words[1:]

    s = ' '.join(words)
    if 'chevin' in s:
        s = 'chevin'

    return s


def normalise():
    with open('rinfo_norm.dat', 'w') as f_norm_rinfo:
        f_norm_rinfo.write('index\tname\n')
        with open('rinfo.dat') as f_rinfo:
            next(f_rinfo)
            for line in f_rinfo:
                words = line.split('\t')
                idx = words[0]
                name = words[1]
                norm_name = normalise_name(name)
                f_norm_rinfo.write('%s\t%s\n' % (idx, norm_name))

    with open('results_norm.dat', 'w') as f_norm_res:
        f_norm_res.write('index\tname\n')
        with open('resulttable.dat') as f_results:
            next(f_results)
            for line in f_results:
                words = line.split('\t')
                idx = words[0]
                name = words[1]
                norm_name = normalise_name(name)
                f_norm_res.write('%s\t%s\n' % (idx, norm_name))

if __name__ == '__main__':
    normalise()
    score = build_result_to_race_index()
    print score
    #build_results_table()
    #build_race_info_table()
    #fr = FellRunner()
    #print list(fr.get_race_ids('2017','3'))
