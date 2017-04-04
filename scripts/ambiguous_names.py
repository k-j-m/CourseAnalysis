import os
from collections import defaultdict
from kcourse.file_tools import read_result_to_race_index, read_results_file


def find_ambiguous_names():
    runner_clubs = defaultdict(set)

    result_folder = 'results'
    fname = 'result_to_race_index.dat'
    result_to_race, _ = read_result_to_race_index(fname)
    for race_id in result_to_race:
        f = os.path.join(result_folder, race_id + '.csv')
        if not os.path.exists(f):
            continue
        for name, club, category, time in read_results_file(f):
            runner_clubs[name].add(club)

    ordered_names = sorted(runner_clubs.iteritems(),
                           reverse=True,
                           key=lambda x: len(x[1]))

    lines = []
    for name, clubs in ordered_names[0:10]:
        lines.append('%s\t%s' % (name, ', '.join(clubs)))
    print '\n'.join(lines)


def print_all_clubs():
    clubs = set()
    result_folder = 'results'
    for f in os.listdir(result_folder):
        fpath = os.path.join(result_folder, f)
        for name, club, category, time in read_results_file(fpath):
            clubs.add(club)

    print '\n'.join(sorted(clubs))


if __name__ == '__main__':
    #  find_ambiguous_names()
    print_all_clubs()
