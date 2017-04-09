"""
Builds a big index of runner race performances then prompts
the user for a runner name to print the history for.
"""
from collections import defaultdict
from kcourse.domain import RunnerRacePerformance, EmptyResultSet


def build_runner_index(data_folder, result_folder):

    runners = defaultdict(list)

    rinfo_table = data_folder.raceinfo
    result_to_race, _ = data_folder.result_to_race_index
    race_theta = data_folder.read_race_theta()

    result_folder.get_resultset('552')
    for result_id, race_id in result_to_race.iteritems():
        if result_id not in result_folder:
            continue

        try:
            resultset = result_folder.get_resultset(result_id)
        except EmptyResultSet:
            continue
        rinfo = rinfo_table[race_id]

        std_time = resultset.winning_time * race_theta[result_id]
        race_name = rinfo.name
        date = rinfo.date
        for result_item in resultset:
            name = result_item.name
            time = result_item.time

            score = 1.0 * time / std_time
            runner_perf = RunnerRacePerformance(result_id, race_id, race_name,
                                                date, time, score)
            runners[name].append(runner_perf)
    return runners


if __name__ == '__main__':
    from kcourse.file_tools import DataFolder, ResultsFolder
    data_folder = DataFolder('data')
    result_folder = ResultsFolder('results')
    runner_index = build_runner_index(data_folder, result_folder)

    while True:
        runner_name = raw_input('Enter runner name:')
        results = runner_index[runner_name.lower()]

        print 'Results for runner: %s' % runner_name
        print '-------------------------------------'
        lines = []
        for item in results:
            lines.append('%s\t%s\t%f' % (item.race_name, item.date, item.score))
        print '\n'.join(lines)
        print '-------------------------------------'