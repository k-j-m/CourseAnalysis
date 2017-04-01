import re


class RetiredRunner(ValueError):
    pass

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
            yield name, club, category, time


def process_results_file(f):
    """
    Munges a results csv file and returns usable data

    Returns:
        Dict[str, int]: mapping of runner name -> finish time (in seconds)
    """
    runners = {}
    for name, club, category, time in read_results_file(f):
        runners[name] = time
    return runners


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