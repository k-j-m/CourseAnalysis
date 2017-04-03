"""
Print out a table of race information, including our new 'duration' parameter
"""
from kcourse.file_tools import RaceInfoTable, read_race_scores, read_result_to_race_index, read_winning_times


def print_race_table():
    race_duration_scores = read_race_scores('race_scores.out')
    results_folder = 'results'
    raceinfo_table = RaceInfoTable('rinfo.dat')
    _, course_to_results = read_result_to_race_index('result_to_race_index.dat')
    winning_times = read_winning_times('winning_times.out')

    lines = ['course_id\tresult_id\tname\tdate\tdist(km)\tclimb(m)\twinning_time(s)\tscore']

    for course_id, name, datestr, dist_km, climb_m in raceinfo_table:
        if course_id not in course_to_results:
            continue
        result_id = course_to_results[course_id]
        if result_id not in race_duration_scores:
            continue
        score = race_duration_scores[result_id]
        twin = winning_times[result_id]
        words = map(str, [course_id, result_id, name, datestr,
                          dist_km, climb_m, twin, score])
        lines.append('\t'.join(words))

    print '\n'.join(lines)


if __name__ == '__main__':
    print_race_table()
