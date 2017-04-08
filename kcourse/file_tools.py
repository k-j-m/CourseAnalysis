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


class BadName(ValueError):
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
            except BadName:
                continue
            yield name, club, category, time


def read_winning_times(f):
    d = {}
    with open(f) as f_in:
        next(f_in)
        for line in f_in:
            words = line.split()
            d[words[0]] = words[1]
    return d


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
    name = name.strip()
    name = name.replace('.', ' ')
    name = ' '.join(name.split())
    if not name:
        raise BadName

    try:
        time = timestr_to_secs(timestr)
    except:
        raise RetiredRunner
    return name, club, category, time


def ends_2_decimals(s):
    pattern = '.*[0-9][0-9]$'
    return re.match(pattern, s)


def timestr_to_secs(s):
    chars = []
    for c in s:
        try:
            int(c)
            chars.append(c)
        except:
            chars.append(' ')

    words = ''.join(chars).split()
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


class ResultItem(object):
    def __init__(self, result_id, position, name, club, category, time):
        self.result_id = result_id
        self.position = position
        self.name = name
        self.club = club
        self.category = category
        self.time = time

    @staticmethod
    def from_csv_line(result_id, csv_line):
        position, name, club, category, time = munge_line(csv_line)
        return ResultItem(result_id, position, name, club, category, time)


class RunnerInfo(object):
    def __init__(self, name, score, race_results):
        self.name = name
        self.score = score
        self.race_result = race_results


class RunnerRacePerformance(object):
    def __init__(self, result_id, race_id, race_name, date, time, score):
        self.result_id = result_id
        self.race_id = race_id
        self.race_name = race_name
        self.date = date
        self.time = time
        self.score = score


class RaceResultSet(object):
    def __init__(self, race_id, result_items):
        if not result_items:
            raise EmptyResultSet(race_id)

        self.race_id = race_id
        self.result_items = result_items
        self._winning_time = None
        self._avg_time = None

    @property
    def winning_time(self):
        if self._winning_time is None:
            self._winning_time = min(ritem.time for ritem in self.result_items)
        return self._winning_time

    @property
    def avg_time(self):
        if self._avg_time is None:
            tot_time = sum(ritem.time for ritem in self.result_items)
            self._avg_time = tot_time / self.num_finishers
        return self._avg_time

    @property
    def num_finishers(self):
        return len(self.result_items)

    def iteritems(self):
        for ritem in self.ritems:
            yield ritem.name, ritem.time

    def __iter__(self):
        return iter(self.result_items)


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
                try:
                    idx, name, datestr, dist_km, climb_m = line.strip().split('\t')
                except ValueError:
                    raise ValueError('Bad line: %s' % line)
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
        race_id, name, datestr, dist_km, climb_m = self._data[idx]
        rinfo = RaceInfo(name, datestr, dist_km, climb_m)
        return rinfo


class DataFolder(object):
    """
    Provides an easy interface for working with the course analysis data folder
    """

    def __init__(self, f):
        self._f = f

    @property
    def raceinfo(self):
        f = os.path.join(self._f, 'rinfo.dat')
        return RaceInfoTable(f)

    @property
    def result_to_race_index(self):
        f = os.path.join(self._f, 'result_to_race_index.dat')
        return read_result_to_race_index(f)

    def read_race_theta(self):
        f = os.path.join(self._f, 'race_theta.out')
        rtheta = {}
        with open(f) as f_in:
            next(f_in)
            for line in f_in:
                rid, strtheta = line.strip().split('\t')
                rtheta[rid] = float(strtheta)
        return rtheta

    def write_winning_times(self, race_ids, winning_times):
        assert len(race_ids) == len(winning_times)
        f = os.path.join(self._f, 'winning_times.out')
        with open(f, 'w') as f_out:
            f_out.write('result_id\twinning_time\n')
            for race_id, twin in izip(race_ids, winning_times):
                f_out.write('%s\t%f\n' % (race_id, twin))

    def write_race_theta0(self, race_ids, race_theta0):
        assert len(race_ids) == len(race_theta0)
        f = os.path.join(self._f, 'initial_race_theta.out')
        with open(f, 'w') as f_out:
            f_out.write('result_id\trace_theta0\n')
            for race_id, theta in izip(race_ids, race_theta0):
                f_out.write('%s\t%f\n' % (race_id, theta))

    def write_runner_theta(self, runner_names, runner_theta):
        assert len(runner_names) == len(runner_theta)
        f = os.path.join(self._f, 'runner_theta.out')
        with open(f, 'w') as f_out:
            f_out.write('result_id\trunner_score\n')
            for name, theta in izip(runner_names, runner_theta):
                f_out.write('%s\t%f\n' % (name, theta))

    def write_sorted_runner_theta(self, runner_names, runner_theta):
        assert len(runner_names) == len(runner_theta)
        std_rnr_theta, std_rnrs = zip(*sorted(zip(runner_theta, runner_names)))
        f = os.path.join(self._f, 'sorted_runner_theta.out')
        with open(f, 'w') as f_out:
            f_out.write('result_id\trunner_score\n')
            for name, theta in izip(std_rnrs, std_rnr_theta):
                f_out.write('%s\t%f\n' % (name, theta))

    def write_race_theta(self, race_ids, race_theta):
        assert len(race_ids) == len(race_theta)
        f = os.path.join(self._f, 'race_theta.out')
        with open(f, 'w') as f_out:
            f_out.write('result_id\trace_theta\n')
            for race_id, theta in izip(race_ids, race_theta):
                f_out.write('%s\t%f\n' % (race_id, theta))

    def write_race_errors(self, race_ids, race_errors):
        lines = ['result_id\tmean_err2']
        for r_id, err in sorted(izip(race_ids, race_errors), reverse=True):
            lines.append('%s\t%f' % (r_id, err))
        f = os.path.join(self._f, 'race_errors.out')
        with open(f, 'w') as f_out:
            f_out.write('\n'.join(lines))

    def write_runner_errs(self, runner_names, runner_errs):
        """
        Args:
            runner_names (List[str])
            runner_errs (List[Dict[int, float]])
        """
        avg_errs = [sum([e**2 for e in x.values()]) / len(x) for x in runner_errs]
        num_races = [len(x) for x in runner_errs]
        srtd = sorted(zip(avg_errs, runner_names, num_races), reverse=True)

        lines = ['name\tmean_err2\tnum_points']
        for err, name, nums in srtd:
            lines.append('%s\t%f\t%i' % (name, err, nums))

        f = os.path.join(self._f, 'runner_errors.out')
        with open(f, 'w') as f_out:
            f_out.write('\n'.join(lines))


class ResultsFolder(object):

    def __init__(self, f):
        self._f = f

    def list_csvs(self):
        for fname in os.listdir(self._f):
            fpath = os.path.join(self._f, fname)
            yield fpath

    def __iter__(self):
        for fname in os.listdir(self._f):
            yield os.path.splitext(fname)[0]

    def values(self):
        for csv in self.list_csvs():
            yield RaceCsv(csv)

    def __contains__(self, race_id):
        fname = os.path.join(self._f, race_id + '.csv')
        return os.path.isfile(fname)

    def __getitem__(self, race_id):
        fname = os.path.join(self._f, race_id + '.csv')
        return RaceCsv(fname)

    def get_resultset(self, result_id):
        fname = os.path.join(self._f, result_id + '.csv')
        csv = RaceCsv(fname)

        items = []
        for i, (name, club, category, time) in enumerate(csv.data_rows()):
            try:
                new_item = ResultItem(result_id, i, name, club, category, time)
                items.append(new_item)
            except (RetiredRunner, BadName):
                continue
        return RaceResultSet(result_id, items)


class RaceCsv(object):

    def __init__(self, f):
        self._f = f
        self._blacklist = None
        self._lines = None

    @property
    def race_id(self):
        fname = os.path.split(self._f)[1]
        return os.path.splitext(fname)[0]

    def __read(self):
        self._lines = open(self._f).readlines()

    def header(self):
        return self._lines[0]

    def data_lines(self):
        if self._lines is None:
            self.__read()
        it = iter(self._lines)
        next(it)
        for line in it:
            yield line

    def runner_names(self):
        for line in self.data_lines():
            words = [w.strip() for w in line.split(',')]
            if len(words) == 5:
                words = [words[1] + ' ' + words[0]] + words[2:]
            name, club, category, time = words
            yield name

    def data_rows(self):
        for line in self.data_lines():
            try:
                name, club, category, time = munge_line(line)
            except RetiredRunner:
                continue
            except BadName:
                continue
            yield name, club, category, time

    def process(self):
        """
        Munges a results csv file and returns usable data

        Returns:
            Dict[str, int]: mapping of runner name -> finish time (in seconds)
        """
        runners = {}
        for name, club, category, time in read_results_file(self._f):
            runners[name] = time

        if not runners:
            raise EmptyResultSet

        return runners
