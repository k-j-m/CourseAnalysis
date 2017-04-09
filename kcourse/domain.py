class RetiredRunner(ValueError):
    pass


class EmptyResultSet(ValueError):
    pass


class BadName(ValueError):
    pass


class ResultItem(object):
    def __init__(self, result_id, position, name, club, category, time):
        self.result_id = result_id
        self.position = position
        self.name = name
        self.club = club
        self.category = category
        self.time = time

    @staticmethod
    def from_csv_line(result_id, csv_line):
        from kcourse.file_tools import munge_line
        position, name, club, category, time = munge_line(csv_line)
        return ResultItem(result_id, position, name, club, category, time)


class RunnerInfo(object):
    def __init__(self, name, score, race_results):
        self.name = name
        self.score = score
        self.race_result = race_results


class RunnerRacePerformance(object):
    def __init__(self, result_id, race_id, race_name, date, time, score):
        self.result_id = result_id
        self.race_id = race_id
        self.race_name = race_name
        self.date = date
        self.time = time
        self.score = score

    def to_json(self):
        return self.__dict__


class RaceResultSet(object):
    def __init__(self, race_id, result_items):
        if not result_items:
            raise EmptyResultSet(race_id)

        self.race_id = race_id
        self.result_items = result_items
        self._winning_time = None
        self._avg_time = None

    @property
    def winning_time(self):
        if self._winning_time is None:
            self._winning_time = min(ritem.time for ritem in self.result_items)
        return self._winning_time

    @property
    def avg_time(self):
        if self._avg_time is None:
            tot_time = sum(ritem.time for ritem in self.result_items)
            self._avg_time = tot_time / self.num_finishers
        return self._avg_time

    @property
    def num_finishers(self):
        return len(self.result_items)

    def iteritems(self):
        for ritem in self.ritems:
            yield ritem.name, ritem.time

    def __iter__(self):
        return iter(self.result_items)


class RaceInfo(object):
    """
    Class to model the data that we want to capture about a specific
    race instance.

    We're capturing all of this info for each year that the race runs
    to give some flexibility for dealing with year-to-year changes in
    the vital statistics.
    """
    def __init__(self, name='', date=None, distance_km=0.0, climb_m=0.0):
        self.name = name
        self.date = date
        self.distance_km = distance_km
        self.climb_m = climb_m

    def to_json(self):
        return {
            'name': self.name,
            'date': self.date,
            'distance_km': self.distance_km,
            'climb_m': self.climb_m,
        }
