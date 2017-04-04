import os
from kcourse.file_tools import read_results_file


def normalise_club1(s):
    s = s.lower()
    s = s.replace('(', '')
    s = s.replace(')', '')
    s = s.replace('  ', ' ')
    s = s.replace('.', '')
    s = s.replace(' running', '')
    s = s.replace(' rc', '')
    s = s.replace(' harriers', '')
    s = s.replace(' harrier', '')
    s = s.replace(' triathlon', 'tri')
    s = s.replace('&', 'and')
    s = s.replace(' club', '')
    return s


def list_clubs():
    folder = 'results'
    clubs = set()
    for f in os.listdir(folder):
        fpath = os.path.join(folder, f)
        for _, club, _, _ in read_results_file(fpath):
            clubs.add(normalise_club1(club))

    print '\n'.join(sorted(clubs))


if __name__ == '__main__':

    list_clubs()