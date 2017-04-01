import os
import re
from itertools import izip


def count_unique_runners():
    runners = set()
    folder = 'results'
    for f in os.listdir(folder):
        fpath = os.path.join(folder, f)
        runners.update(runners_from_results(fpath))
    return len(runners)


def runners_from_results(fpath):
    with open(fpath) as f_in:
        next(f_in)
        for line in f_in:
            try:
                words = [w.strip() for w in line.split(',')]
                if len(words) == 5:
                    words = [words[1] + ' ' + words[0]] + words[2:]
                name, club, category, time = words
                yield name
            except:
                #print fpath
                print line
                raise


def verify_results_files():
    bad_files = []
    folder = 'results'
    for f in os.listdir(folder):
        fpath = os.path.join(folder, f)
        try:
            list(runners_from_results(fpath))
        except:
            bad_files.append(f)
    print '\n'.join(bad_files)
    print len(bad_files)


class RetiredRunner(ValueError):
    pass


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


def process_results_file(f):
    """
    Munges a results csv file and returns usable data

    Returns:
        Dict[str, int]: mapping of runner name -> finish time (in seconds)
    """
    runners = {}
    with open(f) as f_in:
        next(f_in)  # throw away header
        for line in f_in:
            try:
                name, club, category, time = munge_line(line)
            except RetiredRunner:
                pass
            except:
                print f, line,
                #raise
            else:
                runners[name] = time

    return runners


def process_results_collection(race_data_dicts):
    """
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
    return normed_race_dicts, runners


class Scorer(object):

    def __init__(self, races, n_races, n_runners):
        self.races = races
        self.n_races = n_races
        self.n_runners = n_runners

    def unrolled_cost_function(self, params):
        race_scores = [params[i] for i in xrange(self.n_races)]
        runner_scores = [params[i + self.n_races] for
                         i in xrange(self.n_runners)]

        J, race_grads, runner_grads = self.cost_function(race_scores,
                                                         runner_scores)
        grads = race_grads + runner_grads
        #print '@@@', race_grads
        #print '---', grads[0]
        assert len(grads) == self.n_races + self.n_runners
        return J, grads

    def cost_function(self, race_scores, runner_scores):
        """
        Args:
            races (List[Dict[int, int]]): For each race, a dict of
                { runner_id: time_s }
            race_scores (List[float]): list of race duration scores
            runner_scores (List[float]): list of runner handicap scores
        """
        J = 0

        #race_scores, old_race_scores = race_scores[:], race_scores
        #runner_scores, old_runner_scores = runner_scores[:], runner_scores

        # normalise race and runner scores

        race_grads = [0] * len(race_scores)
        runner_grads = [0] * len(runner_scores)

        for race_id, runners in enumerate(self.races):
            d = race_scores[race_id]
            for runner_id, time in runners.iteritems():
                h = runner_scores[runner_id]
                prediction = d * h
                err = time - prediction
                J += 0.5 * err**2
                runner_grads[runner_id] -= d * err
                race_grads[race_id] -= h * err

        return J, race_grads, runner_grads


def calc_avg_race_time(race_data):
    """
    Args:
        race_data (Dict[_, int])
    """
    return 1.0 * sum(race_data.values()) / len(race_data)


def calc_theta0(races, runner_names):
    """
    Args:
        races (List[Dict[str: int]]) - list of race results (each a dict of runner name -> time)
        runner_names (List of runner names)
    """
    from collections import defaultdict
    runner_scores = defaultdict(set)
    race_theta0 = []
    for r in races:
        fastest = None
        for v in r.values():
            if fastest is None or v < fastest:
                fastest = v
        race_theta0.append(fastest)
        for k, v in r.iteritems():
            v_norm = v / fastest
            runner_scores[k].add(v_norm)

    assert len(runner_scores) == len(runner_names)
    runner_theta0 = []
    for nm in runner_names:
        runner_theta0.append(sum(runner_scores[nm]))

    race_theta0 = [calc_avg_race_time(r) for r in races]
    runner_theta0 = [1.] * len(runner_names)
    return race_theta0, runner_theta0



def create_scorer():
    folder = 'results'
    race_dicts = []
    race_ids = []
    for f in os.listdir(folder):
        race_ids.append(f.split('.')[0])
        fpath = os.path.join(folder, f)
        race_data = process_results_file(fpath)
        race_dicts.append(race_data)

    races, runners = process_results_collection(race_dicts)
    scorer = Scorer(races, len(races), len(runners))

    race_theta0, runner_theta0 = calc_theta0(races, runners)

    unrolled_params = race_theta0 + runner_theta0

    J, params = kminimize(scorer.unrolled_cost_function, unrolled_params)

    n_races = len(races)
    n_runners = len(runners)
    race_theta = [params[i] for i in xrange(n_races)]
    runner_theta = [params[i + n_races] for
                     i in xrange(n_runners)]

    sorted_runner_theta, sorted_runners = zip(*sorted(zip(runner_theta, runners)))

    with open('runners.out', 'w') as f_out:
        f_out.write('name\trunner score\n')
        for name, theta in izip(sorted_runners, sorted_runner_theta):
            f_out.write('%s\t%f\n' % (name, theta))

    with open('race_scores.out', 'w') as f_out:
        f_out.write('result_id\tcourse_score\n')
        for race_id, theta in izip(race_ids, race_theta):
            f_out.write('%s\t%f\n' % (race_id, theta))


def kminimize(fun, initial_params):
    n = len(initial_params)
    print 'n:', n
    alpha = 3E-12
    print 'alpha:', alpha

    params = initial_params[:]
    i_iter = 0
    J = 0
    while True:
        #print 'Iteration: %i' % i_iter
        if i_iter > 50:
            break
        i_iter += 1
        J0 = J
        J, grads = fun(params)
        print J
        if i_iter > 1:
            rel_change = (J - J0) / J0
            if rel_change > 1.1:
                raise Exception("Convergence is exploding - reduce learning rate: %f" % alpha)

        for i, grad in enumerate(grads):
            p = params[i]
            p2 = p - alpha * grad
            params[i] = p2


    return J, params


if __name__ == '__main__':
    #verify_results_files()
    #print count_unique_runners()
    create_scorer()
    #import timeit
    #print timeit.timeit('f()', setup='from __main__ import f', number=10)