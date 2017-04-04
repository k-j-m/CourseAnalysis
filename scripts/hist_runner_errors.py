
if __name__ == '__main__':
    import math
    import matplotlib.pyplot as plt

    errors = []
    numraces = []
    totalcount = 0
    initialcount = 0
    with open('runner_errors.out') as f_in:
        next(f_in)
        delta = 1e-6
        for line in f_in:
            words = line.split('\t')
            name = words[0]

            err2 = float(words[1])
            num = int(words[2])
            numraces.append(math.log(num))

            if len(name.replace('.', ' ').split()[0]) == 1:
                initialcount += num
            totalcount += num

            if err2 < delta:
                err2 = delta
            errors.append(math.log(err2))

    race_errors = []
    with open('race_errors.out') as f_in:
        next(f_in)
        for line in f_in:
            err2 = float(line.split('\t')[1])
            race_errors.append(math.log(err2))

    print 'PCT INITIALED: %.2f' % (100. * initialcount / totalcount)

    plt.hist(errors)
    plt.figure()
    plt.hist(numraces)
    plt.figure()
    plt.hist(race_errors)
    plt.show()
