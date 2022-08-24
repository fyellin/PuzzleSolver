import operator
from collections import Counter, defaultdict
from collections.abc import Hashable, Sequence
from datetime import datetime
from itertools import combinations, permutations

from solver import Clue, DancingLinks, Encoder, EquationSolver


class FillInCrosswordGrid:
    grid_size: int
    acrosses: Sequence[tuple[int, str]]
    downs: Sequence[tuple[int, str]]
    encoding: dict[str, tuple[tuple[int], tuple[int]]]
    constraints: dict[Hashable, list[str]]
    optional_constraints: set[str]
    results: list

    def __init__(self, grid_size, acrosses, downs):
        self.grid_size = grid_size
        self.acrosses = acrosses
        self.downs = downs
        self.encoder = Encoder("0123456789/.")
        self.constraints = {}
        self.finder = defaultdict(lambda: defaultdict(list))
        self.optional_constraints = set()
        self.results = []

    def run(self, debug=0):
        self.constraints.clear()
        self.finder.clear()
        self.optional_constraints.clear()
        self.results.clear()

        time1 = datetime.now()

        self.get_across_constraints()
        self.get_down_constraints()
        self.handle_numbering()
        if not self.verify():
            return

        def print_me(solution):
            result = {number: (row, column)
                      for _, *info in solution
                      for number, row, column in info}
            self.results.append(result)

        solver = DancingLinks(self.constraints,
                              optional_constraints=self.optional_constraints,
                              row_printer=print_me)

        solver.solve(debug=debug)
        time2 = datetime.now()
        print(time2 - time1)
        return self.results

    def get_across_constraints_fast(self):
        acrosses = self.acrosses
        length = len(acrosses)
        grid_size = self.grid_size
        if length & 1 == 1:
            assert grid_size & 1 == 1
            number, entry = acrosses[length // 2]
            grid_middle = (grid_size + 1) // 2
            row, column = (grid_middle, grid_middle - len(entry) // 2)
            self.__generate_constraint(True, (number, (row, column), entry))
        elif grid_size & 1:
            grid_middle = (grid_size + 1) // 2
            row, column = grid_middle, grid_middle
        else:
            row, column = grid_size // 2 + 1, 1

        max_locations = {}
        for number, entry in reversed(acrosses[:length // 2]):
            if column <= len(entry):
                row, column = row - 1, grid_size + 1
            column -= len(entry)
            max_locations[number] = (row, column)

        min_locations, row, column = {}, 1, 1
        for (number, entry) in acrosses[:length // 2]:
            if column + len(entry) > grid_size + 1:
                row, column = row + 1, 1
            min_locations[number] = (row, column)
            column += len(entry)

        for index, (number1, entry1) in enumerate(acrosses[:(length - 1) // 2]):
            number2, entry2 = acrosses[~index]
            assert len(entry1) == len(entry2)
            for row1, col1 in self.__iterate_squares(
                    min_locations[number1], max_locations[number1]):
                row2, col2 = grid_size + 1 - row1, grid_size + 2 - col1 - len(entry1)
                self.__generate_constraint(True, (number1, (row1, col1), entry1),
                                           (number2, (row2, col2), entry2))

    def get_across_constraints_slow(self):
        acrosses = self.acrosses
        if len(acrosses) & 1 == 1:
            assert self.grid_size & 1 == 1
            number, entry = acrosses[len(acrosses) // 2]
            grid_middle = (self. grid_size + 1) // 2
            row, column = (grid_middle, grid_middle - len(entry) // 2)
            self.__generate_constraint(True, (number, (row, column), entry))

        for index, (number1, entry1) in enumerate(acrosses[:(len(acrosses) - 1) // 2]):
            number2, entry2 = acrosses[~index]
            assert len(entry1) == len(entry2)
            locations = self.__locations_for_size_across(len(entry1))
            for (row1, column1), (row2, column2) in locations:
                self.__generate_constraint(True, (number1, (row1, column1), entry1),
                                           (number2, (row2, column2), entry2))

    get_across_constraints = get_across_constraints_fast

    def get_down_constraints(self):
        downs = self.downs
        # We don't yet handle odd-sized down-clues
        assert len(downs) & 1 == 0
        size_to_clue = defaultdict(list)
        for (number, entry) in downs:
            size_to_clue[len(entry)].append((number, entry))
        for size, entries in size_to_clue.items():
            locations = self.__locations_for_size_down(size)
            for (number1, entry1), (number2, entry2) in combinations(entries, 2):
                for (row1, column1), (row2, column2) in locations:
                    self.__generate_constraint(False, (number1, (row1, column1), entry1),
                                               (number2, (row2, column2), entry2))

    # This generates constraints items of the form clue1@location~clue2, e.g. 4A@r2c3~7D.
    # This constraint is added to all rows for clue2 which are inconsistent to clue1 being
    # at the given location.  (In the example given, all cases in which 7D which are
    # less than or equal to location r2c3.)  It is also added to all rows for clue1 which
    # place it precisely at that location.
    # By adding all such constraint items, we force the numbers to be in the correct
    # order
    #
    # Normally, we need a unique optional constraint for each pair of rows we want to
    # make mutually exclusive.  If we use the same constraint to make both A1 and B
    # mutually exclusive as we do to make A2 and B, mutually exclusive, we end up also
    # making A1 and A2 mutually exclusive, even if that wasn't the case.  It's okay
    # here because we're excluding things that would already be excluded anyway as they
    # are the same clue number
    def handle_numbering(self):
        operators = [operator.lt, operator.eq, operator.gt]
        clues = [*((number, 'A') for number, _ in self.acrosses),
                 *((number, 'D') for number, _ in self.downs)]
        for clue1, clue2 in permutations(clues, 2):
            finder1, finder2 = self.finder[clue1], self.finder[clue2]
            assert finder1 and finder2
            (number1, letter1), (number2, letter2) = clue1, clue2
            # returns op.lt, op.eq, or op.gt such that op(number1, number2) is true
            op = operators[(number1 >= number2) + (number1 > number2)]
            assert op(number1, number2)
            for location1, values1 in finder1.items():
                row1, column1 = location1
                item = None # only set item if we need it.
                for location2, values2 in finder2.items():
                    if not op(location1, location2):
                        item = item or \
                               f'{number1}{letter1}@r{row1}c{column1}~{number2}{letter2}'
                        for value in values2:
                            value.append(item)
                if item is not None:
                    assert item not in self.optional_constraints
                    self.optional_constraints.add(item)
                    for value in values1:
                        value.append(item)

    def __generate_constraint(self, is_across, *clue_location_entry):
        letter = 'A' if is_across else 'D'
        name = letter, *((number, row, column)
                         for number, (row, column), _ in clue_location_entry)
        info = [f'Entry-{letter}{number}' for number, _, _ in clue_location_entry]
        info_length = len(info)
        for number, (row, column), entry in clue_location_entry:
            dr, dc = (0, 1) if is_across else (1, 0)
            locations = [(row + i * dr, column + i * dc) for i in range(len(entry))]
            for location, ch in zip(locations, entry):
                info.extend(self.encoder.encode(ch, location, is_across))
        self.constraints[name] = info
        self.optional_constraints.update(info[info_length:])
        for number, (row, column), entry in clue_location_entry:
            self.finder[(number, letter)][row, column].append(info)

    def __locations_for_size_across(self, size):
        result = []
        for row1 in range(1, self.grid_size + 1):
            for col1 in range(1, self.grid_size + 2 - size):
                row2, col2 = self.grid_size + 1 - row1, self.grid_size + 2 - col1 - size,
                if (row1, col1) >= (row2, col2):
                    continue
                if row1 == row2 and col2 < col1 + size:
                    continue
                result.append(((row1, col1), (row2, col2)))
        return result

    def __locations_for_size_down(self, size):
        result = []
        for row1 in range(1, self.grid_size + 2 - size):
            for col1 in range(1, self.grid_size + 1):
                row2, col2 = self.grid_size + 2 - row1 - size, self.grid_size + 1 - col1
                if (row1, col1) >= (row2, col2):
                    continue
                if col1 == col2 and row2 < row1 + size:
                    continue
                result.append(((row1, col1), (row2, col2)))
        return result

    def __iterate_squares(self, min_location, max_location):
        r, c = min_location
        end_row, end_column = max_location
        while True:
            yield r, c
            if (r, c) == (end_row, end_column):
                break
            if c == self.grid_size:
                r, c = r + 1, 1
            else:
                c += 1

    def verify(self):
        ok = True
        for constraint, values in self.constraints.items():
            if len(values) != len(set(values)):
                ok = False
                counter = Counter(values)
                print(constraint, *(x for x, count in counter.items() if count > 1))
        return ok

    def display(self, locations):
        clues = [Clue(f'{number}{letter}', is_across,
                      locations[number], len(entry), context=entry)
                 for letter, clues in (('A', self.acrosses), ('D', self.downs))
                 for is_across in [letter == 'A']
                 for number, entry in clues]
        clue_answers = {clue: clue.context for clue in clues}
        printer = EquationSolver(clues)
        printer.plot_board(clue_answers, font_multiplier=0.5)


def main():
    acrosses = (
        (1, '161051'), (5, '2985984'), (10, '406.125'), (12, '3.125'),
        (13, '1105'), (15, '681503'), (16, '56006721'), (19, '24137569'), (20, '738639'),
        (21, '725760'), (23, '2/15'),
        (25, '49.28'),
        (27, '10/7'), (29, '916839'),
        (31, '170625'), (33, '16777559'), (37, '33534749'), (38, '326592'), (39, '1904'),
        (40, '651.7'), (41, '912.673'), (42, '8168202'), (43, '234256'))

    downs = (
        (1, '1485172'), (2, '161078'), (3, '0.008'), (4, '5156/343'), (5, '25/243'),
        (6, '83853'), (7, '5.12'), (8, '9150570'), (9, '45369'), (11, '161172'),
        (14, '1729'), (17, '266/23'), (18, '23/169'), (22, '287/3123'), (24, '1679616'),
        (26, '995328'), (28, '7529536'), (30, '153/92'), (31, '1955'), (32, '607062'),
        (33, '10368'), (34, '70972'), (35, '149.4'), (36, '85.8'))

    filler = FillInCrosswordGrid(13, acrosses, downs)
    results = filler.run(debug=1000)
    for result in results:
        filler.display(result)


if __name__ == '__main__':
    main()
