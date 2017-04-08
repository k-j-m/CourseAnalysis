import re
import os
from itertools import izip

from kcourse.file_tools import (EmptyResultSet, DataFolder, ResultsFolder)


def count_unique_runners():
    runners = set()
    folder = 'results'
    res_folder = ResultsFolder(folder)
    for res_csv in res_folder.values():
        runners.update(res_csv.runner_names())
    return len(runners)


def process_results_collection(race_data_dicts):
    """
    TODO: ITS HERE ITS HERE! IT MUST BE HERE!
    Args:
        race_data_dicts (Iter[RaceResultSet])

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

    return normed_race_dicts, runners


class Scorer(object):

    def __init__(self, races, n_races, n_runners, winning_times):
        self.races = races
        self.n_races = n_races
        self.n_runners = n_runners
        self.winning_times = winning_times

    def unrolled_cost_function(self, params):
        race_scores = [params[i] for i in xrange(self.n_races)]
        runner_scores = [params[i + self.n_races] for
                         i in xrange(self.n_runners)]

        J, race_grads, runner_grads = self.cost_function(race_scores,
                                                         runner_scores)
        grads = race_grads + runner_grads
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

        race_grads = [0] * len(race_scores)
        runner_grads = [0] * len(runner_scores)

        count = 0
        for race_id, runners in enumerate(self.races):
            d = race_scores[race_id]
            twin = self.winning_times[race_id]
            for runner_id, time in runners.iteritems():
                h = runner_scores[runner_id]
                prediction = d * h * twin
                err = (time - prediction) / time
                J += 0.5 * err**2
                runner_grads[runner_id] -= d * err * twin / time
                race_grads[race_id] -= h * err * twin / time
                count += 1

        J_norm = J / count
        race_grads_norm = [rg / count for rg in race_grads]
        runner_grads_norm = [rg / count for rg in runner_grads]
        return J_norm, race_grads_norm, runner_grads_norm

    def race_errors(self, race_scores, runner_scores):
        for race_id, runners in enumerate(self.races):
            d = race_scores[race_id]
            twin = self.winning_times[race_id]
            count = 0
            J = 0
            for runner_id, time in runners.iteritems():
                h = runner_scores[runner_id]
                prediction = d * h * twin
                err = (time - prediction) / time
                J += 0.5 * err**2
                count += 1
            yield J / count

    def runner_errors(self, race_scores, runner_scores):
        runner_errs = [{} for _ in runner_scores]
        for race_id, runners in enumerate(self.races):
            d = race_scores[race_id]
            twin = self.winning_times[race_id]
            for runner_id, time in runners.iteritems():
                h = runner_scores[runner_id]
                prediction = d * h * twin
                err = (time - prediction) / time
                runner_errs[runner_id][race_id] = err
        return runner_errs


def calc_avg_race_time(race_data):
    """
    Args:
        race_data (Dict[_, int])
    """
    return 1.0 * sum(race_data.values()) / len(race_data)


def min_race_time(race_data):
    return min(race_data.values())


def get_races_and_runners(data_folder, results_fpath):
    folder = results_fpath
    result_folder = ResultsFolder(folder)
    result_to_race, _ = data_folder.result_to_race_index
    rinfo_table = data_folder.raceinfo  # used to check race names
    ignore_patterns = ['trunce']

    race_dicts = []
    race_ids = []

    for result_id in result_to_race:
        race_id = result_to_race[result_id]  # TODO: use iteritems()
        race_name = rinfo_table[race_id].name
        for ig_patt in ignore_patterns:
            if re.match(ig_patt, race_name, re.IGNORECASE):
                continue

        if result_id not in result_folder:
            continue

        try:
            race_data = result_folder[result_id].process()
        except EmptyResultSet:
            continue

        race_ids.append(result_id)
        race_dicts.append(race_data)
    races, runners = process_results_collection(race_dicts)
    return races, runners, race_ids


def create_scorer2(races, runners, winning_times):
    scorer = Scorer(races, len(races), len(runners), winning_times)
    return scorer


def create_scorer(data_folder, niters, J_logger_fn=None):
    races, runners, race_ids = get_races_and_runners(data_folder, 'results')
    winning_times = [min_race_time(r) for r in races]
    runner_theta0 = [1.] * len(runners)
    race_theta0 = [1.0 for _ in winning_times]
    unrolled_params = race_theta0 + runner_theta0

    scorer = create_scorer2(races, runners, winning_times)
    J, params = kminimize(scorer.unrolled_cost_function,
                          unrolled_params, niters, J_logger_fn)

    n_races = len(races)
    n_runners = len(runners)
    race_theta = [params[i] for i in xrange(n_races)]
    runner_theta = [params[i + n_races] for
                    i in xrange(n_runners)]

    J3, _ = scorer.unrolled_cost_function(params)
    J2, _, _ = scorer.cost_function(race_theta, runner_theta)
    assert J3 == J2, 'Error: %f != %f' % (J, J2)

    # Write a bunch of stuff back out to the output folder
    data_folder.write_winning_times(race_ids, winning_times)
    data_folder.write_runner_theta(runners, runner_theta)
    data_folder.write_sorted_runner_theta(runners, runner_theta)
    data_folder.write_race_theta(race_ids, race_theta)

    race_errs = scorer.race_errors(race_theta, runner_theta)
    data_folder.write_race_errors(race_ids, race_errs)

    runner_errs = scorer.runner_errors(race_theta, runner_theta)
    data_folder.write_runner_errs(runners, runner_errs)


def kminimize(fun, initial_params, niters, J_logger_fn=None):
    if J_logger_fn is None:
        J_logger_fn = lambda x: None

    n = len(initial_params)
    print 'n:', n
    alpha = 1000.
    print 'alpha:', alpha

    params = initial_params[:]
    i_iter = 0
    J = 0
    while True:
        #print 'Iteration: %i' % i_iter
        if i_iter > niters:
            break
        i_iter += 1
        J0 = J
        J, grads = fun(params)
        J_logger_fn(J)
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

    J_vals = []
    def J_logger(J):
        J_vals.append(J)

    #check_initial_vals()
    #import time
    #start_time = time.time()
    data_folder = DataFolder('data')
    create_scorer(data_folder, niters=50, J_logger_fn=J_logger)
    print '\n'.join(map(str, J_vals))
    #print 'Elapsed time: %f' % (time.time() - start_time)

    #import timeit
    #print timeit.timeit('f()', setup='from __main__ import f', number=10)
