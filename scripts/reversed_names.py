import os


def has_reversed_names(f):
    num_spaces = 0
    with open(f) as f_in:
        header = next(f_in)
        for line in f_in:
            words = line.split(',')
            if len(words) == 4:
                return False
            if ' ' in words[0]:
                num_spaces += 1
    if num_spaces > 3:
        return False

    return True


def fix_reversed_names(f):
    lines = []
    with open(f) as f_in:
        lines.append(next(f_in))
        for line in f_in:
            words = line.split(',')
            assert len(words) > 4, line
            #assert ' ' not in words[0]
            first_name = words[1].strip()
            surname = words[0].strip()
            full_name = first_name + ' ' + surname
            words = [full_name] + words[2:]
            lines.append(','.join(words))

    with open(f, 'w') as f_out:
        f_out.write(''.join(lines))


def reverse_names(f):
    lines = []
    with open(f) as f_in:
        lines.append(next(f_in))
        for line in f_in:
            words = line.split(',')
            surname, given_names = words[0].split(' ', 1)
            words[0] = given_names + ' ' + surname
            lines.append(','.join(words))
    with open(f, 'w') as f_out:
        f_out.write(''.join(lines))


def bad_results_file(f):
    with open(f) as f_in:
        header = next(f_in)
        for line in f_in:
            words = line.split(',')
            if len(words) > 4:
                return True
    return False


def prompt():
    while True:
        s = raw_input('>> Enter file name: ')
        if not s:
            continue
        reverse_names(os.path.join('results', s))

if __name__ == '__main__':
    prompt()
    folder = 'results'
    #fix_reversed_names(os.path.join(folder, '1656.csv'))
    for f in os.listdir(folder):
        fpath = os.path.join(folder, f)
        if bad_results_file(fpath):
        #if has_reversed_names(fpath):
        #    fix_reversed_names(fpath)
            print f
    