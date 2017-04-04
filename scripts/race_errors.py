import analysis


def read_race_theta():
    f = 'race_theta.out'
    thetas = []
    with open(f) as f_in:
        next(f_in)
        for line in f_in:
            th = float(line.split().strip()[1])
            thetas.append(th)
    return thetas


def read_runner_theta():
    f = 'runner_theta.out'
    thetas = []
    with open(f) as f_in:
        next(f_in)
        for line in f_in:
            th = float(line.split().strip()[1])
            thetas.append(th)
    return thetas


if __name__ == '__main__':
    races, runners, race_ids = analysis.get_races_and_runners()
    winning_times = [analysis.min_race_time(r) for r in races]
    scorer = analysis.create_scorer2(races, runners, winning_times)
    race_theta = read_race_theta()
    runner_theta = read_runner_theta()

    with open('race_errors.out', 'w') as f_out:
        f_out.write('result_id\tmean_err2\n')
        lines = []
        for r_id, err in sorted(scorer.race_errors(race_theta, runner_theta),
                                key=lambda x: x[1],
                                reverse=True):
            race_id = race_ids[r_id]
            lines.append('%s\t%f' % (race_id, err))
        f_out.write('\n'.join(lines))
