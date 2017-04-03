import os
from itertools import izip
from kcourse.file_tools import RaceInfoTable, read_result_to_race_index, process_results_file, process_results_collection, read_results_file


def calc_race_times(result_data):
    min_ = min(result_data.values())
    mean = 1.0 * sum(result_data.values()) / len(result_data)
    return min_, mean


def print_times():
    folder = 'results'
    result_to_race, _ = read_result_to_race_index('result_to_race_index.dat')
    raceinfo_table = RaceInfoTable('rinfo.dat')

    race_dicts = []
    race_ids = []
    for result_id in result_to_race:
    #for f in os.listdir(folder):
        fpath = os.path.join(folder, result_id + '.csv')
        if not os.path.exists(fpath):
            continue

        race_ids.append(result_id)
        race_data = process_results_file(fpath)
        race_dicts.append(race_data)

    races, runners = process_results_collection(race_dicts)

    lines = ['race_id\tresult_id\tname\tdate\tdist\tclimb\twinner\tavg']
    for result_id, result_data in izip(race_ids, races):
        min_, mean = calc_race_times(result_data)
        race_id = result_to_race[result_id]
        _, name, datestr, dist_km, climb_m = raceinfo_table[race_id]

        words = map(str, [race_id, result_id, name, datestr, dist_km, climb_m, min_, mean])
        lines.append('\t'.join(words))
    print '\n'.join(lines)


def check_bishophill():
    f = os.path.join('results','676.csv')
    for items in read_results_file(f):
        print '\t'.join(map(str, items))

    data = process_results_file(f)
    print calc_race_times(data)

if __name__ == '__main__':
    #print_times()
    check_bishophill()