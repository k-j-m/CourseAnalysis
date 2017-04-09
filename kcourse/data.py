import os
from itertools import izip
import cStringIO as StringIO

from kcourse.domain import RaceInfo, ResultItem, RaceResultSet, RetiredRunner, BadName
from kcourse.file_tools import read_result_to_race_index, munge_line, read_results_file


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
                    datestr = normalise_date(datestr)

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

    def raw_csv(self):
        with open(self._f) as f:
            s = f.read()
        return StringIO.StringIO(s)

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


def normalise_date(s):
    """
    Format the fellrunner.org.uk format D-M-YYYY in to the ISO8601
    compliant YYYY-MM-DD
    """
    dd, mm, yy = s.split('-')
    dd = str(int(dd)).zfill(2)
    mm = str(int(mm)).zfill(2)
    assert len(yy) == 4
    int(yy)
    return '%s-%s-%s' % (yy, mm, dd)
