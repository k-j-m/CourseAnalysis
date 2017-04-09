import re

from kcourse.domain import RetiredRunner, BadName


def read_race_scores(f):
    d = {}
    with open(f) as f_in:
        next(f_in)  # throw away header
        for line in f_in:
            idx, scorestr = line.split()
            d[idx] = float(scorestr)
    return d


def read_result_to_race_index(fpath):
    """
    Reads the race_to_result index file as a couple of dictionaries, giving
    a bi-directional mapping between the two.

    Returns:
        Tuple[Dict[str, str], Dict[str, str]]
    """
    result_to_race = {}
    race_to_result = {}
    with open(fpath) as f_in:
        next(f_in)
        for line in f_in:
            result_index, race_index = line.split()
            result_to_race[result_index] = race_index
            race_to_result[race_index] = result_index
    return result_to_race, race_to_result


def read_results_file(f):
    """
    Steps through a results file and processes and yields each
    line in turn.
    """
    with open(f) as f_in:
        next(f_in)  # throw away header
        for line in f_in:
            try:
                name, club, category, time = munge_line(line)
            except RetiredRunner:
                continue
            except BadName:
                continue
            yield name, club, category, time


def read_winning_times(f):
    d = {}
    with open(f) as f_in:
        next(f_in)
        for line in f_in:
            words = line.split()
            d[words[0]] = words[1]
    return d


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
    name = name.strip()
    name = name.replace('.', ' ')
    name = ' '.join(name.split())
    if not name:
        raise BadName

    try:
        time = timestr_to_secs(timestr)
    except:
        raise RetiredRunner
    return name, club, category, time


def ends_2_decimals(s):
    pattern = '.*[0-9][0-9]$'
    return re.match(pattern, s)


def timestr_to_secs(s):
    chars = []
    for c in s:
        try:
            int(c)
            chars.append(c)
        except:
            chars.append(' ')

    words = ''.join(chars).split()
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
