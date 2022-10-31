import operator
from collections import Counter, defaultdict
from collections.abc import Hashable, Sequence
from datetime import datetime
from functools import cache
from itertools import chain, combinations, count, permutations
from typing import Optional

from solver import Clue, DancingLinks, Encoder, EquationSolver

Square = tuple[int, int]


class FillInCrosswordGridAbstract:
    width: int
    height: int
    encoding: dict[str, tuple[tuple[int], tuple[int]]]
    constraints: dict[Hashable, list[str]]
    optional_constraints: set[str]
    results: list

    def __init__(self, *, width: Optional[int] = None, height: Optional[int] = None,
                 size: Optional[int] = None, alphabet: str):
        if size is not None:
            self.width = self.height = size
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        assert self.width is not None and self.height is not None
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
            self.get_grid_constraints(full)
            if numbering:
                self.handle_numbering()
            if not black_squares_okay:
                self.prohibit_black_squares()
            if not self.verify():
                return []
            self.finder.clear()  # big, and not needed anymore

            def print_me(solution):
                result = [clue for constraint in solution
                          if isinstance(constraint, Sequence)
                          for clue in constraint
                          if isinstance(clue, Clue)]
                self.results.append(result)

            total = sum(len(items) for items in self.constraints.values())
            print(f"The constraints have total length {total}")
            solver = DancingLinks(self.constraints,
                                  optional_constraints=self.optional_constraints,
                                  row_printer=print_me)

            solver.solve(debug=debug)
            return self.results
        finally:
            time2 = datetime.now()
            print(time2 - time1)

    def get_grid_constraints(self, full):
        raise Exception

    def verify(self) -> bool:
        ok = True
        for constraint, values in self.constraints.items():
            if len(values) != len(set(values)):
                ok = False
                counter = Counter(values)
                print(constraint, *(x for x, length in counter.items() if length > 1))
        return ok

    def display(self, clues: list[Clue]) -> None:
        clue_answers = {clue: clue.context for clue in clues}
        printer = EquationSolver(clues)
        printer.plot_board(clue_answers, font_multiplier=1)

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
        clues = list(self.finder.keys())
        for clue1, clue2 in permutations(clues, 2):
            finder1, finder2 = self.finder[clue1], self.finder[clue2]
            (number1, letter1), (number2, letter2) = clue1, clue2
            # Create a function consistent() such that consistent(location1, location2)
            # indicates whether clue number1 in location1 and clue number2 in location2
            # are consistent possibilites
            delta = number2 - number1
            if delta > 0:
                def consistent(loc1: Square, loc2: Square) -> bool:
                    return self._square_index(loc2) - self._square_index(loc1) >= delta
            elif delta < 0:
                def consistent(loc1: Square, loc2: Square) -> bool:
                    return self._square_index(loc2) - self._square_index(loc1) <= delta
            else:
                consistent = operator.eq

            for location1, values1 in finder1.items():
                row1, column1 = location1
                item = None  # only set item if we need it.
                for location2, values2 in finder2.items():
                    if not consistent(location1, location2):
                        item = item or \
                               f'{number1}{letter1}@r{row1}c{column1}|{number2}{letter2}'
                        for value in values2:
                            value.append(item)
                if item is not None:
                    assert item not in self.optional_constraints
                    self.optional_constraints.add(item)
                    for value in values1:
                        value.append(item)

    def _square_index(self, square: Square) -> int:
        """Converts the square into a one-based index"""
        (row, column) = square
        return (row - 1) * self.width + column

    @cache
    def _locations_for_size_across(self, size: int) -> Sequence[tuple[Square, Square]]:
        height, width = self.height, self.width
        result = []
        for row1, row2 in zip(count(1), count(height, -1)):
            for column1, column2 in zip(count(1), range(width + 1 - size, 0, -1)):
                if (row1, column1) >= (row2, column2):
                    return result
                if row1 == row2 and column2 < column1 + size:
                    continue
                result.append(((row1, column1), (row2, column2)))

    def _locations_for_size_down(self, size: int) -> Sequence[tuple[Square, Square]]:
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

    def prohibit_black_squares(self) -> None:
        """
        Prohibit black squares by creating height * width * 2 constraints indicating that
        each square has been covered by an across clue and a bottom clue.  We also
        create additional entries in the constraints table, one for each constraint above,
        so that the missing constraints can be added if necessary.  But we don't allow
        both missing across and missing down for the same square.
        """
        encoder = self.encoder
        locators = {((row, column), is_across): encoder.locator((row, column), is_across)
                    for row in range(1, self.height + 1)
                    for column in range(1, self.width + 1)
                    for is_across in [True, False]}
        not_both = {(row, column): f'r{row}c{column}-not-both-unclued'
                    for row in range(1, self.height + 1)
                    for column in range(1, self.width + 1)
                    }

        for constraint_name, constraint in self.constraints.items():
            if isinstance(constraint_name, Sequence):
                constraint.extend(locators[location, clue.is_across]
                                  for clue in constraint_name
                                  for location in clue.locations)

        for ((row, col), is_across), locator in locators.items():
            constraint_name = f'Unclued-{row}-{col}-{is_across}'
            self.constraints[constraint_name] = [locator, not_both[row, col]]

        self.optional_constraints.update(not_both.values())

    def _generate_constraint(self, is_across: bool,
                             *clue_location_entry: tuple[int, Square, str],
                             extras: Sequence[str] = ()) -> None:
        name = tuple(self._get_clue(number, entry, row, column, is_across)
                     for number, (row, column), entry in clue_location_entry)
        # The optional items, first
        info = [item
                for clue in name
                for location, ch in zip(clue.locations, clue.context)
                for item in self.encoder.encode(ch, location, is_across)]
        self.optional_constraints.update(info)
        info.extend(f'Clue-{clue.context}' for clue in name)
        info.extend(extras)
        self.constraints[name] = info

        for number, (row, column), entry in clue_location_entry:
            self.finder[(number, is_across)][row, column].append(info)

    @staticmethod
    @cache
    def _get_clue(number, entry, row, column, is_across):
        letter = 'A' if is_across else 'D'
        return Clue(f'{number}{letter}', is_across, (row, column), len(entry), context=entry)

class FillInCrosswordGrid (FillInCrosswordGridAbstract):
    acrosses: Sequence[tuple[int, str]]
    downs: Sequence[tuple[int, str]]

    def __init__(self, acrosses: Sequence[tuple[int, str]],
                 downs: Sequence[tuple[int, str]],
                 *, width: Optional[int] = None, height: Optional[int] = None,
                 size: Optional[int] = None):
        alphabet = ''.join(sorted({x for _, entry in chain(acrosses, downs)
                                   for x in entry}))
        self.acrosses = acrosses
        self.downs = downs
        super().__init__(width=width, height=height, size=size, alphabet=alphabet)

    def get_grid_constraints(self, full):
        if not full:
            self.get_across_constraints_optimal()
        else:
            self.get_across_constraints_full()
        self.get_down_constraints()

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
                self._generate_constraint(True,
                                          (number1, (row1, col1), entry1),
                                          (number2, (row2, col2), entry2))

    def get_across_constraints_full(self) -> None:
        acrosses = self.acrosses
        if len(acrosses) & 1 == 1:
            self._handle_central_across()

        for index, (number1, entry1) in enumerate(acrosses[:len(acrosses) // 2]):
            number2, entry2 = acrosses[~index]
            assert len(entry1) == len(entry2)
            locations = self._locations_for_size_across(len(entry1))
            for location1, location2, in locations:
                ix1, ix2 = self._square_index(location1), self._square_index(location2)
                # The index of the starting square must be at least as large as the
                # clue number, and the difference between the starting squares must
                # be at least as large as the difference between the clue numbers.
                if ix1 < number1 or ix2 < number2 or ix2 - ix1 < number2 - number1:
                    continue
                self._generate_constraint(True, (number1, location1, entry1),
                                                (number2, location2, entry2))

    def _handle_central_across(self) -> Square:
        acrosses, width, height = self.acrosses, self.width, self.height
        number, entry = acrosses[len(acrosses) // 2]
        assert height & 1 == 1  # must be odd height
        assert (width - len(entry)) & 1 == 0  # width and central entry have same parity
        # Set row, column to the starting location of this entry
        row, column = (height + 1) // 2, 1 + (width - len(entry)) // 2
        self._generate_constraint(True, (number, (row, column), entry))
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
                # adding a special constraint item should be helpful.
                self._generate_constraint(False, (number, location, entry),
                                          extras=['Middle'])

        for size, entries in clues_by_size.items():
            locations = self._locations_for_size_down(size)
            for (number1, entry1), (number2, entry2) in combinations(entries, 2):
                for location1, location2 in locations:
                    ix1, ix2 = self._square_index(location1), self._square_index(location2)
                    # The index of the starting square must be at least as large as the
                    # clue number, and the difference between the starting squares must
                    # be at least as large as the difference between the clue numbers.
                    if ix1 < number1 or ix2 < number2 or ix2 - ix1 < number2 - number1:
                        continue
                    self._generate_constraint(False,
                                              (number1, location1, entry1),
                                              (number2, location2, entry2))

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

class FillInCrosswordGridMushed (FillInCrosswordGridAbstract):
    clues: Sequence[tuple[int, str]]

    def __init__(self, clues: Sequence[tuple[int, str]],
                 *, width: Optional[int] = None, height: Optional[int] = None,
                 size: Optional[int] = None):
        alphabet = ''.join(sorted({x for _, entry in clues for x in entry}))
        self.clues = clues
        super().__init__(width=width, height=height, size=size, alphabet=alphabet)

    def get_grid_constraints(self, _full: bool) -> None:
        clues = self.clues
        clues_by_size = defaultdict(list)
        for (number, entry) in clues:
            clues_by_size[len(entry)].append((number, entry))

        self.handle_odd_size_counts(clues_by_size)
        self.handle_paired_entries(clues_by_size)

    def handle_paired_entries(self, clues_by_size: dict[int, list[tuple[int, str]]]) -> None:
        for size, entries in clues_by_size.items():
            across_locations = self._locations_for_size_across(size)
            down_locations = self._locations_for_size_down(size)
            for locations in (across_locations, down_locations):
                is_across = locations is across_locations
                for (number1, entry1), (number2, entry2) in combinations(entries, 2):
                    if number1 == number2:
                        continue
                    for location1, location2 in locations:
                        ix1, ix2 = self._square_index(location1), self._square_index(
                            location2)
                        # The index of the starting square must be at least as large as the
                        # clue number, and the difference between the starting squares must
                        # be at least as large as t
                        # he difference between the clue numbers.
                        if ix1 < number1 or ix2 < number2 or ix2 - ix1 < number2 - number1:
                            continue
                        self._generate_constraint(is_across,
                                                  (number1, location1, entry1),
                                                  (number2, location2, entry2))

    def handle_odd_size_counts(self, clues_by_size: dict[int, list[tuple[int, str]]]) -> None:
        # This code is not yet tested.
        # We also need to add additional items, such as MIDDLE or MIDDLE-ACROSS and
        # MIDDLE-DOWN to ensure we get at least one of these when necessary
        odd_counts = [length for length, v in clues_by_size.items() if len(v) & 1]

        def generate_centered_entry_for_size(
                size: int, is_across: bool, extras: Sequence[str] = ()) -> int:
            if is_across:
                if size > self.width or (size - self.width) ^ 1 == 0:
                    return 0
                location = (self.height + 1) // 2, 1 + (self.width - size) // 2
            else:
                if size > self.height or (size - self.height) ^ 1 == 0:
                    return 0
                location = 1 + (self.height - size) // 2, (self.width + 1) // 2
            for number, entry in clues_by_size[size]:
                self._generate_constraint(is_across, (number, location, entry),
                                           extras=extras)
            return len(clues_by_size[size])

        if len(odd_counts) == 0:
            if self.width & 1 == 1 and self.height & 1 == 1:
                for size in clues_by_size.keys():
                    if size & 1 == 1:
                        a, d = f'Middle-{size}-A', f'Middle-{size}-D'
                        generate_centered_entry_for_size(size, True, [a])
                        generate_centered_entry_for_size(size, False, [d])
                        # To keep parity, we need either both of these, or neither.
                        # We add a new constraint row for the none case.
                        self.constraints[f'Middle-{size}-both-or-none'] = [a, d]

        elif len(odd_counts) == 1:
            odd_count = odd_counts[0]
            count = 0
            extras = f'Middle-{odd_count}',
            if self.width & 1 == 1:
                count += generate_centered_entry_for_size(odd_count, True, extras)
            if self.height & 1 == 1:
                count += generate_centered_entry_for_size(odd_count, False, extras)
            if count == 0:
                raise Exception("No way to handle odd number of clues")

        elif len(odd_counts) == 2:
            assert self.width & 1 == 1 and self.height & 1 == 1
            assert odd_counts[0] & 1 == 1 and odd_counts[1] & 1 == 1
            for odd_count in odd_counts:
                # We don't know which one length is across and which is down, but we know
                # we need exactly one across, one down, and one for each odd length, so
                # we might as well use that fact
                extra = f'Middle-{odd_count}'
                generate_centered_entry_for_size(odd_count, False, (extra, 'MIDDLE-DOWN'))
                generate_centered_entry_for_size(odd_count, True, (extra, 'MIDDLE-ACROSS'))

        else:
            raise Exception("No way to handle more than three odd counts")


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

def test3():
    info = (
         (1, '1737'), (1, '195'), (2, '72'), (3, '731'), (4, '13'), (4, '179'), (5, '35'),
         (6, '92'), (7, '3375'), (8, '512'), (9, '171'), (10, '242'), (11, '196'),
         (12, '608'), (13, '27'), (13, '2744'), (14, '10'), (14, '14'), (15, '71'),
         (16, '2048')
    )
    filler = FillInCrosswordGridMushed(info, width=6, height=5)
    # filler = FillInCrosswordGrid(info, width=7, height=7)
    results = filler.run(debug=3, black_squares_okay=False, numbering=True)
    for result in results:
        filler.display(result)


if __name__ == '__main__':
    test1()
    test2()
    test3()
