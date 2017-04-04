"""
This script find out how many sets of results list the runners' names
with the first name as an initial instead of in full.

It prints out the percentage that use initial-form names followed
by a list of all of the culprit results files.
"""
import os
import analysis


def uses_initials(names):
    """
    Args:
        names (Iter[str])
    """
    for nm in names:
        words = nm.split()
        if not words:
            continue
        if len(words[0]) == 1:
            return True
    return False


def main():
    folder = 'results'
    files = os.listdir(folder)
    culprits = []
    for f in files:
        fpath = os.path.join(folder, f)
        race_results = analysis.process_results_file(fpath)
        if uses_initials(race_results):
            culprits.append(f)

    print 'Percentage using initials: %.2f%%' % (1.0 * len(culprits) / len(files))
    print '\n'.join(culprits)


if __name__ == '__main__':
    main()
