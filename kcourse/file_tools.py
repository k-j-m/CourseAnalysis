import os
import re
from itertools import izip

def read_race_scores(f):
    d = {}
    with open(f) as f_in:
        next(f_in)  # throw away header
        for line in f_in:
            idx, scorestr = line.split()
            d[idx] = float(scorestr)
    return d


class RetiredRunner(ValueError):
    pass


class EmptyResultSet(ValueError):
    pass


def read_result_to_race_index(fpath):
    """
    Reads the race_to_result index file as a couple of dictionaries, giving
    a bi-directional mapping between the two.

    Returns:
        Tuple[Dict[str, str], Dict[str, str]]
    """
    result_to_race = {}
    race_to_result = {}
    with open(fpath) as f_in:
        next(f_in)
        for line in f_in:
            result_index, race_index = line.split()
            result_to_race[result_index] = race_index
            race_to_result[race_index] = result_index
    return result_to_race, race_to_result


def read_results_file(f):
    """
    Steps through a results file and processes and yields each
    line in turn.
    """
    with open(f) as f_in:
        next(f_in)  # throw away header
        for line in f_in:
            try:
                name, club, category, time = munge_line(line)
            except RetiredRunner:
                continue
            yield name, club, category, time


def process_results_collection(race_data_dicts):
    """
    TODO: ITS HERE ITS HERE! IT MUST BE HERE!
    Args:
        race_data_dicts (Iter[Dict[str, int]])

    Returns:
        List[Dict[runner_id, runner_time]]
        List[runner_name]
    """
    runner_index = {}
    runners = []  # list of runner names
    normed_race_dicts = []
    for race_dict in race_data_dicts:
        d = {}
        for runner_name, runner_time in race_dict.iteritems():
            if runner_name not in runner_index:
                runner_index[runner_name] = len(runners)
                runners.append(runner_name)
            runner_id = runner_index[runner_name]
            d[runner_id] = runner_time
        if d:
            normed_race_dicts.append(d)

    for d, dd in izip(race_data_dicts, normed_race_dicts):
        min1 = min(d.values())
        min2 = min(d.values())
        assert min1 == min2  # normed and un-normed must have the same winning time

    print '***:', min(race_data_dicts[1076].values())
    return normed_race_dicts, runners


def read_winning_times(f):
    d = {}
    with open(f) as f_in:
        next(f_in)
        for line in f_in:
            words = line.split()
            d[words[0]] = words[1]
    return d


def process_results_file(f):
    """
    Munges a results csv file and returns usable data

    Returns:
        Dict[str, int]: mapping of runner name -> finish time (in seconds)
    """
    runners = {}
    for name, club, category, time in read_results_file(f):
        runners[name] = time

    if not runners:
        raise EmptyResultSet

    return runners


RETIRED = set(['ret', 'retired', 'dnf', 'dq', 'unknown',
               'n/a', 'late', 'd.n.s', 'retd'])


def munge_line(s):
    words = [w.strip() for w in s.lower().split(',')]
    if len(words) == 5:
        words = [words[1] + ' ' + words[0]] + words[2:]
    name, club, category, timestr = words
    name.replace('twitter', '')
    name = name.replace('facebook', '')
    name = name.replace('strava', '')
    if not ends_2_decimals(timestr) or timestr.isdigit():
        raise RetiredRunner
    if re.match('.*[a-z].*', timestr):
        raise RetiredRunner
    time = timestr_to_secs(timestr)
    return name, club, category, time


def ends_2_decimals(s):
    pattern = '.*[0-9][0-9]$'
    return re.match(pattern, s)


def timestr_to_secs(s):
    s = s.replace('-', ':')
    s = s.replace('/', ':')
    s = s.replace('.', ':')
    s = s.replace(' ', ':')
    s2 = None
    while s != s2:
        s2 = s
        s = s.replace('::', ':')
    words = s.split(':')  # split(delimiters=[':', '-', '/'], string=s)
    words = [w if w else '0' for w in words]
    ints = map(int, words)
    if len(ints) == 3:
        return 3600 * ints[0] + 60 * ints[1] + ints[2]
    else:
        assert len(ints) == 2
        return 60 * ints[0] + ints[1]


def split(delimiters, string, maxsplit=0):
    import re
    regexPattern = '|'.join(map(re.escape, delimiters))
    return re.split(regexPattern, string, maxsplit)


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


class RaceInfoTable(object):

    def __init__(self, f):
        if not os.path.exists(f):
            with open(f, 'w') as f_out:
                f_out.write('index\tname\tdate\tdistance_km\tclimb_m\n')
        self._f = f

        self._data = {}
        with open(f) as f_in:
            next(f_in) # throw away header
            for line in f_in:
                idx, name, datestr, dist_km, climb_m = line.strip().split('\t')
                self._data[idx] = idx, name, datestr, dist_km, climb_m

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

    def race_ids(self):
        return iter(self.data)

    def __getitem__(self, idx):
        return self._data[idx]
