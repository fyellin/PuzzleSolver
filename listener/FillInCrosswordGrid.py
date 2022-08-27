import operator
from collections import Counter, defaultdict
from collections.abc import Hashable, Mapping, Sequence
from datetime import datetime
from functools import cache
from itertools import chain, combinations, count, permutations
from typing import Optional

from solver import Clue, DancingLinks, Encoder, EquationSolver

Square = tuple[int, int]


class FillInCrosswordGrid:
    width: int
    height: int
    acrosses: Sequence[tuple[int, str]]
    downs: Sequence[tuple[int, str]]
    encoding: dict[str, tuple[tuple[int], tuple[int]]]
    constraints: dict[Hashable, list[str]]
    optional_constraints: set[str]
    results: list

    def __init__(self, acrosses: Sequence[tuple[int, str]],
                 downs: Sequence[tuple[int, str]],
                 *, width: Optional[int] = None, height: Optional[int] = None,
                 size: Optional[int] = None):
        if size is not None:
            self.width = self.height = size
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        assert self.width is not None and self.height is not None
        alphabet = ''.join(sorted({x for _, entry in chain(acrosses, downs)
                                   for x in entry}))
        self.acrosses = acrosses
        self.downs = downs
        self.encoder = Encoder.of(alphabet)
        self.constraints = {}
        self.optional_constraints = set()
        self.finder = defaultdict(lambda: defaultdict(list))
        self.results = []

    def run(self, *, debug=0,
            full: bool = False, numbering: bool = True, black_squares_okay: bool = False):
        self.constraints.clear()
        self.finder.clear()
        self.optional_constraints.clear()
        self.results.clear()

        time1 = datetime.now()

        try:
            self.get_across_constraints(full)
            self.get_down_constraints()
            if numbering:
                self.handle_numbering()
            if not black_squares_okay:
                self.prohibit_black_squares()
            if not self.verify():
                return []
            self.finder.clear()  # big, and not needed anymore

            def print_me(solution):
                result = {clue: (row, column)
                          for rows in solution
                          for (clue, _type, row, column) in rows
                          # number being a string is used for other stuff.
                          if not isinstance(clue, str)}
                self.results.append(result)

            solver = DancingLinks(self.constraints,
                                  optional_constraints=self.optional_constraints,
                                  row_printer=print_me)

            solver.solve(debug=debug)
            return self.results
        finally:
            time2 = datetime.now()
            print(time2 - time1)

    def get_across_constraints(self, full):
        if not full:
            self.get_across_constraints_optimal()
        else:
            self.get_across_constraints_full()

    def get_across_constraints_optimal(self) -> None:
        acrosses, width, height = self.acrosses, self.width, self.height
        length = len(acrosses)
        if (length & 1) == 1:
            row, column = self._handle_central_across()
        else:
            # Set row, column to the square just beyond the first half of the
            # grid.  This is just beyond where the first half of the across clues can go
            if height & 1 == 0:
                row, column = height // 2, width + 1
            else:
                row, column = (height + 1) // 2, 1 + width // 2

        max_locations = {}
        for number, entry in reversed(acrosses[:length // 2]):
            if column <= len(entry):
                row, column = row - 1, width + 1
            column -= len(entry)
            max_locations[number] = (row, column)

        min_locations, row, column = {}, 1, 1
        for (number, entry) in acrosses[:length // 2]:
            if column + len(entry) > width + 1:
                row, column = row + 1, 1
            min_locations[number] = (row, column)
            column += len(entry)

        for index, (number1, entry1) in enumerate(acrosses[:length // 2]):
            number2, entry2 = acrosses[~index]
            assert len(entry1) == len(entry2)
            for row1, col1 in self.__iterate_squares(
                    len(entry1), min_locations[number1], max_locations[number1]):
                row2, col2 = height + 1 - row1, width + 2 - col1 - len(entry1)
                self.__generate_constraint(True, (number1, (row1, col1), entry1),
                                           (number2, (row2, col2), entry2))

    def get_across_constraints_full(self) -> None:
        acrosses = self.acrosses
        if len(acrosses) & 1 == 1:
            self._handle_central_across()

        for index, (number1, entry1) in enumerate(acrosses[:len(acrosses) // 2]):
            number2, entry2 = acrosses[~index]
            assert len(entry1) == len(entry2)
            locations = self.__locations_for_size_across(len(entry1))
            for location1, location2, in locations:
                ix1, ix2 = self.__sq_ix(location1), self.__sq_ix(location2)
                # The index of the starting square must be at least as large as the
                # clue number, and the difference between the starting squares must
                # be at least as large as the difference between the clue numbers.
                if ix1 < number1 or ix2 < number2 or ix2 - ix1 < number2 - number1:
                    continue
                self.__generate_constraint(True, (number1, location1, entry1),
                                                 (number2, location2, entry2))

    def _handle_central_across(self) -> Square:
        acrosses, width, height = self.acrosses, self.width, self.height
        number, entry = acrosses[len(acrosses) // 2]
        assert height & 1 == 1  # must be odd height
        assert (width - len(entry)) & 1 == 0  # width and central entry have same parity
        # Set row, column to the starting location of this entry
        row, column = (height + 1) // 2, 1 + (width - len(entry)) // 2
        self.__generate_constraint(True, (number, (row, column), entry))
        return row, column

    def get_down_constraints(self) -> None:
        downs = self.downs
        clues_by_size = defaultdict(list)
        for (number, entry) in downs:
            clues_by_size[len(entry)].append((number, entry))

        odd_counts = [length for length, v in clues_by_size.items() if len(v) & 1]
        if len(downs) & 1 == 0:
            # There must be an even number of every clue length
            assert len(odd_counts) == 0
        else:
            # There must be only one clue length with an odd number of clues
            assert len(odd_counts) == 1
            entry_length = odd_counts[0]
            assert self.width & 1 == 1  # must be odd width
            assert (self.height - entry_length) & 1 == 0  # same parity
            location = 1 + (self.height - entry_length) // 2, (self.width + 1) // 2
            for number, entry in clues_by_size[entry_length]:
                # There should only be a few clues that can go in the middle, so
                # creating this as a constraint should be helpful.
                self.__generate_constraint(False, (number, location, entry),
                                           extras=['Middle'])

        for size, entries in clues_by_size.items():
            locations = self.__locations_for_size_down(size)
            for (number1, entry1), (number2, entry2) in combinations(entries, 2):
                for location1, location2 in locations:
                    ix1, ix2 = self.__sq_ix(location1), self.__sq_ix(location2)
                    # The index of the starting square must be at least as large as the
                    # clue number, and the difference between the starting squares must
                    # be at least as large as the difference between the clue numbers.
                    if ix1 < number1 or ix2 < number2 or ix2 - ix1 < number2 - number1:
                        continue
                    self.__generate_constraint(False, (number1, location1, entry1),
                                               (number2, location2, entry2))

    def handle_numbering_old(self) -> None:
        """
        Add constraints items to the clues to ensure that the numbering is in order.

        This generates constraint items of the form clue1@location|clue2,
        for example, 4A@r2c3|7D.

        This constraint is added to two sets of constraint rows:
        A) All rows that place clue1 at the indicated location, In this case, all clues
           indicating that 4A starts at r2c3
        B) All rows that place clue2 at a location that is inconsistent with clue1 being
           at location.  In this example, since 7 > 4, clue 7D must start after 4A, and
           we add this constraint to any row which causes 7D to start before r2c3.

        Normally, we need a unique optional constraint item for each pair of rows that
        are mutually exclusive.  If we make both A mutually exclusive with both B1 and B2
        using the same constraint item, B1 and B2 end up being mutually exclusive.  It's
        okay here.
        """
        operators = [operator.lt, operator.eq, operator.gt]
        clues = [*((number, 'A') for number, _ in self.acrosses),
                 *((number, 'D') for number, _ in self.downs)]
        for clue1, clue2 in permutations(clues, 2):
            finder1, finder2 = self.finder[clue1], self.finder[clue2]
            assert finder1, f'Need results for {clue1}'
            assert finder2, f'Need results for {clue2}'
            (number1, letter1), (number2, letter2) = clue1, clue2
            # returns op.lt, op.eq, or op.gt such that op(number1, number2) is true
            op = operators[(number1 >= number2) + (number1 > number2)]
            assert op(number1, number2)
            for location1, values1 in finder1.items():
                row1, column1 = location1
                item = None  # only set item if we need it.
                for location2, values2 in finder2.items():
                    if not op(location1, location2):
                        item = item or \
                               f'{number1}{letter1}@r{row1}c{column1}|{number2}{letter2}'
                        for value in values2:
                            value.append(item)
                if item is not None:
                    assert item not in self.optional_constraints
                    self.optional_constraints.add(item)
                    for value in values1:
                        value.append(item)

    def handle_numbering(self) -> None:
        """
        Add constraints items to the clues to ensure that the numbering is in order.

        This generates constraint items of the form clue1@location|clue2,
        for example, 4A@r2c3|7D.

        This constraint is added to two sets of constraint rows:
        A) All rows that place clue1 at the indicated location, In this case, all
           constraint rows indicating that 4A starts at r2c3
        B) All rows that place clue2 at a location that is inconsistent with clue1 being
           at location.  In this example, since 7 - 4 = 3, clue 7D must start at least
           three squares after 4A, and so we mark all constraint rows indicating that
           7D starts before r2c6.

        Normally, we need a unique optional constraint item for each pair of rows that
        are mutually exclusive.  If we make both A mutually exclusive with both B1 and B2
        using the same constraint item, B1 and B2 end up being mutually exclusive.  It's
        okay here.
        """
        clues = [*((number, 'A') for number, _ in self.acrosses),
                 *((number, 'D') for number, _ in self.downs)]
        for clue1, clue2 in permutations(clues, 2):
            finder1, finder2 = self.finder[clue1], self.finder[clue2]
            assert finder1, f'Need results for {clue1}'
            assert finder2, f'Need results for {clue2}'
            (number1, letter1), (number2, letter2) = clue1, clue2
            delta = number2 - number1
            if delta > 0:
                def op(loc1: Square, loc2: Square) -> bool:
                    return self.__sq_ix(loc2) - self.__sq_ix(loc1) >= delta
            elif delta < 0:
                def op(loc1: Square, loc2: Square) -> bool:
                    return self.__sq_ix(loc2) - self.__sq_ix(loc1) <= delta
            else:
                op = operator.eq
            # returns op.lt, op.eq, or op.gt such that op(number1, number2) is true
            # op = operators[(number1 >= number2) + (number1 > number2)]
            for location1, values1 in finder1.items():
                row1, column1 = location1
                item = None  # only set item if we need it.
                for location2, values2 in finder2.items():
                    if not op(location1, location2):
                        item = item or \
                               f'{number1}{letter1}@r{row1}c{column1}|{number2}{letter2}'
                        for value in values2:
                            value.append(item)
                if item is not None:
                    assert item not in self.optional_constraints
                    self.optional_constraints.add(item)
                    for value in values1:
                        value.append(item)

    def prohibit_black_squares(self) -> None:
        """
        Prohibit black squares by creating height * width * 2 constraints indicating that
        each square has been covered by an across clue and a bottom clue.  We also
        create additional entries in the constraints table, one for each constraint above,
        so that the missing constraints can be added if necessary.  But we don't allow
        both missing across and missing down for the same square.
        """
        encoder = self.encoder
        locators = {(row, column, is_across): encoder.locator((row, column), is_across)
                    for row in range(1, self.height + 1)
                    for column in range(1, self.width + 1)
                    for is_across in [True, False]}
        not_both = {(row, column): f'r{row}c{column}-not-both-unclued'
                    for row in range(1, self.height + 1)
                    for column in range(1, self.width + 1)
                    }
        for clue_list, is_across in (self.acrosses, True), (self.downs, False):
            dr, dc = (0, 1) if is_across else (1, 0)
            for number, entry in clue_list:
                finder = self.finder[number, "A" if is_across else "D"]
                for (row, column), constraints in finder.items():
                    clue_locators = [locators[row + i * dr, column + i * dc, is_across]
                                     for i in range(len(entry))]
                    for constraint in constraints:
                        constraint.extend(clue_locators)

        for (row, col, is_across), locator in locators.items():
            letter = 'A' if is_across else 'D'
            constraint_name = ('Unclued', letter, row, col),
            self.constraints[constraint_name] = [locator, not_both[row, col]]

        self.optional_constraints.update(not_both.values())

    def __generate_constraint(self, is_across: bool,
                              *clue_location_entry: tuple[int, Square, str],
                              extras: Sequence[str] = ()) -> None:
        letter = 'A' if is_across else 'D'
        name = tuple((number, letter, row, column)
                     for number, (row, column), _ in clue_location_entry)
        info = [f'Clue-{number}{letter}' for number, _, _ in clue_location_entry]
        info.extend(extras)
        for number, (row, column), entry in clue_location_entry:
            dr, dc = (0, 1) if is_across else (1, 0)
            locations = [(row + i * dr, column + i * dc) for i in range(len(entry))]
            for location, ch in zip(locations, entry):
                encoding = self.encoder.encode(ch, location, is_across)
                self.optional_constraints.update(encoding)
                info.extend(encoding)
        self.constraints[name] = info
        for number, (row, column), entry in clue_location_entry:
            self.finder[(number, letter)][row, column].append(info)

    @cache
    def __locations_for_size_across(self, size: int) -> Sequence[tuple[Square, Square]]:
        height, width = self.height, self.width
        result = []
        for row1, row2 in zip(count(1), count(height, -1)):
            for column1, column2 in zip(count(1), range(width + 1 - size, 0, -1)):
                if (row1, column1) >= (row2, column2):
                    return result
                if row1 == row2 and column2 < column1 + size:
                    continue
                result.append(((row1, column1), (row2, column2)))

    def __locations_for_size_down(self, size: int) -> Sequence[tuple[Square, Square]]:
        height, width = self.height, self.width
        result = []
        for row1, row2 in zip(count(1), count(height + 1 - size, -1)):
            for column1, column2 in zip(range(1, width + 1), range(width, 0, -1)):
                if (row1, column1) >= (row2, column2):
                    return result
                # If there is a middle column, we have to make sure they don't overlap.
                if column1 == column2 and row2 < row1 + size:
                    continue
                result.append(((row1, column1), (row2, column2)))

    def __iterate_squares(self, size: int, min_location: Square, max_location: Square
                          ) -> Sequence[Square]:
        r, c = min_location
        end_row, end_column = max_location
        while True:
            yield r, c
            if (r, c) == (end_row, end_column):
                break
            if c + size - 1 == self.width:
                r, c = r + 1, 1
            else:
                c += 1

    @cache
    def __sq_ix(self, square: Square) -> int:
        """Converts the square into a one-based index"""
        (row, column) = square
        return (row - 1) * self.width + column

    def verify(self) -> bool:
        ok = True
        for constraint, values in self.constraints.items():
            if len(values) != len(set(values)):
                ok = False
                counter = Counter(values)
                print(constraint, *(x for x, length in counter.items() if length > 1))
        return ok

    def display(self, locations: Mapping[int, Square]) -> None:
        clues = [Clue(f'{number}{letter}', is_across,
                      locations[number], len(entry), context=entry)
                 for letter, clues in (('A', self.acrosses), ('D', self.downs))
                 for is_across in [letter == 'A']
                 for number, entry in clues]
        clue_answers = {clue: clue.context for clue in clues}
        printer = EquationSolver(clues)
        printer.plot_board(clue_answers, font_multiplier=0.5)


def test1():
    acrosses = (
        (1, '161051'), (5, '2985984'), (10, '406.125'), (12, '3.125'),
        (13, '1105'), (15, '681503'), (16, '56006721'), (19, '24137569'), (20, '738639'),
        (21, '725760'), (23, '2/15'),
        (25, '49.28'),
        (27, '10/7'), (29, '916839'),
        (31, '170625'), (33, '16777559'), (37, '33534749'), (38, '326592'), (39, '1904'),
        (40, '651.7'), (41, '912.673'), (42, '8168202'), (43, '234256'))

    downs = (
        (1, '1485172'), (2, '161078'), (3, '0.008'), (4, '5156/343'),
        (5, '25/243'),
        (6, '83853'), (7, '5.12'), (8, '9150570'), (9, '45369'), (11, '161172'),
        (14, '1729'),
        # (16.5, "243.153"),
        (17, '266/23'), (18, '23/169'),
        (22, '287/3123'), (24, '1679616'),
        (26, '995328'), (28, '7529536'),
        (30, '153/92'),
        (31, '1955'), (32, '607062'),
        (33, '10368'), (34, '70972'), (35, '149.4'), (36, '85.8'))

    filler = FillInCrosswordGrid(acrosses, downs, size=13)
    results = filler.run(debug=3, black_squares_okay=False, numbering=True, full=True)
    for result in results:
        filler.display(result)


def test2():
    acrosses = [(1, '3541'), (4, '1331'), (8, '2156'), (10, '322'), (12, '324'),
                (14, '45'), (16, '664'), (17, '6416'), (18, '35245'), (19, '51'),
                (21, '64'), (23, '63245'), (25, '2153'), (27, '632'), (29, '54'),
                (30, '314'), (31, '561'), (33, '2512'), (35, '5356'), (36, '3316')]
    downs = [(1, '3136'), (2, '512656'), (3, '42'), (5, '36445'), (6, '3141'), (7, '16'),
             (9, '1314631'), (11, '242'), (13, '2653641'), (15, '5625'), (18, '3125'),
             (20, '143641'), (22, '45325'), (24, '265'), (26, '1463'), (28, '2116'),
             (32, '35'), (34, '23')]
    filler = FillInCrosswordGrid(acrosses, downs, width=8, height=10)
    results = filler.run(debug=3, black_squares_okay=False, full=True)
    # results = filler.no_numbering().run(debug=3)
    for result in results:
        filler.display(result)


if __name__ == '__main__':
    test1()
