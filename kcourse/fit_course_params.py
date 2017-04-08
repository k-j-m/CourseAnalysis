"""
Fits a model to the available course parameters
"""
import numpy
import scipy.optimize
from itertools import izip


def read_result_summary_table(f):
    """
    Reads the summary table produced by our learning algorithm and returns
    a number of lists of column-wise data.

    Returned items:
        0: course_ids (List[str])
        1: result_ids (List[str])
        2: names (List[str])
        3: dates (List[str])
        4: distances (List[float]): course distance in km
        5: climbs (List[float]): course climbs in m
        6: win_times (List[float]): winning time in s
        7: course_scores (List[float]): course correction score (derived by learning algorithm)
    """
    course_ids = []
    result_ids = []
    names = []
    dates = []
    distances = []
    climbs = []
    win_times = []
    course_scores = []

    with open(f) as f_in:
        next(f_in)
        for line in f_in:
            words = line.split('\t')
            (course_id, result_id, name, datestr,
             diststr, climbstr, win_timestr, scorestr) = words

            course_ids.append(course_id)
            result_ids.append(result_id)
            names.append(name)
            dates.append(datestr)
            distances.append(float(diststr))
            climbs.append(float(climbstr))

            win_times.append(float(win_timestr))
            course_scores.append(float(scorestr))

    return course_ids, result_ids, names, dates, distances, climbs, win_times, course_scores


def learn_params(f):
    (course_ids, result_ids, names, dates, distances,
     climbs, win_times, course_scores) = read_result_summary_table(f)

    np_dists = numpy.array(distances)
    np_climbs = numpy.array(climbs)
    np_twins = numpy.array(win_times)
    np_cscores = numpy.array(course_scores)

    print '~~~', np_dists.size

    np_cduration = np_twins * np_cscores
    np_gradients = 0.001 * np_climbs / np_dists

    avg_pace = (np_twins / np_dists).sum()
    k_p0 = 1.0
    k_pm0 = 0.0
    k_c0 = 0.0

    def h((k_c, k_p, k_pm)):

        # find the climb-corrected distance
        np_climbcorrs = k_c * np_gradients
        np_dists_c = np_dists * (1 + np_climbcorrs)

        pace = avg_pace * k_p * (1 + k_pm * np_dists_c)
        print pace
        t_pred = pace * np_dists_c
        return t_pred

    def cost((k_c, k_p, k_pm)):
        t_pred = h((k_c, k_p, k_pm))
        errs = (t_pred - np_cduration) / np_cduration
        return (errs * errs).sum()

    result = scipy.optimize.minimize(fun=cost, x0=(k_c0, k_p0, k_pm0))
    # class A: pass
    # result = A()
    # result.x = [-0.71621488,  1.1003494,   0.01406075]
    print result.x
    print 'kc:', result.x[0]
    print 'p0:', avg_pace * result.x[1]
    print 'pm:', result.x[2]

    print 'err2:', cost(result.x)

    lines = ['course_id\tgnarliness']
    predictions = h(result.x)
    for course_id, t_actual, t_pred in izip(course_ids, np_cduration, predictions):
        gnarliness = t_actual / t_pred
        lines.append('%s\t%f' % (course_id, gnarliness))

    with open('gnarliness.out', 'w') as f_out:
        f_out.write('\n'.join(lines))

    with open('')


if __name__ == '__main__':
    learn_params('resulttable.dat')
