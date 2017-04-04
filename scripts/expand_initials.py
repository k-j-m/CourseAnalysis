import os
from collections import defaultdict
from kcourse.file_tools import timestr_to_secs, process_results_file


def build_result_standard_finish_index():
    f = 'race_theta.out'
    scores = {}
    with open(f) as f_in:
        next(f_in)
        for line in f_in:
            idx, scorestr = line.split()
            scores[idx] = float(scorestr)

    folder = 'results'
    times = {}
    for nm, score in scores.iteritems():
        f = os.path.join(folder, nm + '.csv')
        results = process_results_file(f)
        win_time = min(results.values())
        times[nm] = win_time * scores[nm]
    return times


def build_runner_index():
    initialed_runners = defaultdict(set)
    f = 'runner_ranking.out'
    with open(f) as f_in:
        next(f_in)
        for line in f_in:
            try:
                name, strfloat = line.strip().split('\t')
            except:
                print f
                print line
                raise
            score = float(strfloat)
            names = name.strip().split()
            if len(names) == 1:
                continue
            if len(names[0]) == 1:
                continue
            initialed_name = names[0][0] + ' ' + ' '.join(names[1:])
            initialed_runners[initialed_name].add((name, score))
    return initialed_runners


def expand_initials(runner_index, standard_race_times):
    folder = 'results'
    for race_id in standard_race_times:
        fpath = os.path.join(folder, race_id + '.csv')
        runners = process_results_file(fpath)
        std_time = standard_race_times[race_id]
        for r in runners:
            if len(r.split()[0]) == 1:
                runner_score = 1.0 * runners[r] / std_time
                options = runner_index[r]
                soptions = sorted(options, key=lambda x: abs(x[1]/runner_score - 1))
                print '(%s, %f): %s' % (r, runner_score, soptions)


if __name__ == '__main__':
    std_race_times = build_result_standard_finish_index()
    runner_index = build_runner_index()
    expand_initials(runner_index, std_race_times)
