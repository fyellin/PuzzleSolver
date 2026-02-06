import re
from collections import Counter, defaultdict
from collections.abc import Hashable, Sequence
from datetime import datetime
from functools import cache
from itertools import combinations, count, pairwise
from typing import Iterable, Optional

from solver import Clue, DancingLinks, EquationSolver, Orderer

Square = tuple[int, int]


class FillInCrosswordGridAbstract:
    width: int
    height: int
    encoding: dict[str, tuple[tuple[int], tuple[int]]]
    constraints: dict[Hashable, list[str]]
    optional_constraints: set[str]
    results: list

    def __init__(self, *, width: Optional[int] = None, height: Optional[int] = None,
                 size: Optional[int] = None):
        if size is not None:
            self.width = self.height = size
        if width is not None:
            self.width = width
        if height is not None:
            self.height = height
        assert self.width is not None and self.height is not None
        self.constraints = {}
        self.optional_constraints = set()
        self.finder = defaultdict(lambda: defaultdict(list))
        self.results = []

    def run(self, *, debug=0,
            full: bool = True, numbering: bool = True, black_squares_okay: bool = False):
        self.constraints.clear()
        self.finder.clear()
        self.optional_constraints = {f'r{r}c{c}' for r in range(1, self.height + 1)
                                     for c in range(1, self.width + 1)}
        self.results.clear()

        time1 = datetime.now()

        try:
            self.get_grid_constraints(full)
            if numbering:
                self.handle_numbering()
            self.handle_black_squares(black_squares_okay);
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
            solver = DancingLinks(
                self.constraints,
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
        clue_answers = {clue: clue.context for clue in clues if clue.context}
        printer = EquationSolver(clues)
        printer.plot_board(clue_answers, font_multiplier=1)

    def handle_numbering(self) -> None:
        """
        Add constraints items to the clues to ensure that the numbering is in order.

        The clues are sorted by number, and then adjacent clues are looked at. If they
        are equal, (one being across, the other down), then we ensure they both go into
        the same location.  If they are not equal, we ensure that the first goes to a
        location prior to the second.
        """
        clues = sorted(self.finder.keys())
        for index, (clue1, clue2) in enumerate(pairwise(clues)):
            (number1, letter1), (number2, letter2) = clue1, clue2
            locations = sorted(self.finder[clue1].keys() | self.finder[clue2].keys())
            locations_map = {location: index for index, location in enumerate(locations)}
            prefix = f'{number1}{'da'[letter1]}/{number2}{'da'[letter2]}'
            orderer_type = Orderer.LT if number1 < number2 else Orderer.EQ
            orderer = orderer_type(prefix, len(locations_map))
            self.optional_constraints.update(orderer.all_codes())
            for clue, ordering in ((clue1, orderer.left), (clue2, orderer.right)):
                for location, values in self.finder[clue].items():
                    ordering_constraints = ordering(locations_map[location])
                    for value in values:
                        value.extend(ordering_constraints)

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
        return result

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
        return result

    def handle_black_squares(self, black_squares_okay: bool) -> None:
        """
        Prohibit black squares by creating height * width * 2 constraints indicating that
        each square has been covered by an across clue and a bottom clue.  We also
        create additional entries in the constraints table, one for each constraint above,
        so that the missing constraints can be added if necessary.  But we don't allow
        both missing across and missing down for the same square.
        """
        if black_squares_okay:
            self.optional_constraints |= {f'r{r}c{c}{suffix}'
                                          for r in range(1, self.height + 1)
                                          for c in range(1, self.width + 1)
                                          for suffix in ("-a", "-d")}
        else:
            for row in range(1, self.height + 1):
                for column in range(1, self.width + 1):
                    t = f'r{row}c{column}'
                    needer = f"At-Least-One-{t}"
                    self.constraints[f'Provide-{t}-a'] = [f'{t}-a', needer]
                    self.constraints[f'Provide-{t}-d'] = [f'{t}-d', needer]
                    self.optional_constraints.add(needer)


    def _generate_constraint(self,
                             *clue_location_entry: tuple[int, bool, Square, str | int],
                             extras: Sequence[str] = ()) -> None:
        name = tuple(self._get_clue(number, entry, row, column, is_across)
                     for number, is_across, (row, column), entry in clue_location_entry)
        # The optional items, first
        info: list[str | tuple[str, str]] = [
            f'r{r}c{c}-{"da"[clue.is_across]}'
            for clue in name for (r, c) in clue.locations]

        info.extend(
            (f'r{r}c{c}', ch)
            for clue in name if clue.context
            for (r, c), ch in zip(clue.locations, clue.context))
        info.extend(f'Clue-{clue.context if clue.context else clue.name}' for clue in name)
        info.extend(extras)
        self.constraints[name] = info

        for number, is_across, (row, column), entry in clue_location_entry:
            self.finder[(number, is_across)][row, column].append(info)

    def _iterate_squares(self, size: int, min_location: Square, max_location: Square
                          ) -> Iterable[Square]:
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


    class MyClue(Clue):
        def __str__(self):
            r, c = self.base_location
            return f"<{self.name}@r{r}c{c}>"

    @classmethod
    @cache
    def _get_clue(cls, number, entry, row, column, is_across):
        clue_name = cls._get_clue_name(number, is_across)
        if isinstance(entry, str):
            length, context = len(entry), entry
        else:
            length, context = entry, None
        return cls.MyClue(clue_name, is_across,
                          (row, column), length, context=context)

    @classmethod
    def _get_clue_name(cls, number, is_across):
        return f'{number}{"DA"[is_across]}'


class FillInCrosswordGrid (FillInCrosswordGridAbstract):
    acrosses: Sequence[tuple[int, str]]
    downs: Sequence[tuple[int, str]]

    def __init__(self, acrosses: Sequence[tuple[int, str]],
                 downs: Sequence[tuple[int, str]],
                 *, width: Optional[int] = None, height: Optional[int] = None,
                 size: Optional[int] = None):
        self.acrosses = acrosses
        self.downs = downs
        super().__init__(width=width, height=height, size=size)

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
            for row1, col1 in self._iterate_squares(
                    len(entry1), min_locations[number1], max_locations[number1]):
                row2, col2 = height + 1 - row1, width + 2 - col1 - len(entry1)
                self._generate_constraint((number1, True, (row1, col1), entry1),
                                          (number2, True, (row2, col2), entry2))

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
                self._generate_constraint((number1, True, location1, entry1),
                                          (number2, True, location2, entry2))

    def _handle_central_across(self) -> Square:
        acrosses, width, height = self.acrosses, self.width, self.height
        number, entry = acrosses[len(acrosses) // 2]
        assert height & 1 == 1  # must be odd height
        assert (width - len(entry)) & 1 == 0  # width and central entry have same parity
        # Set row, column to the starting location of this entry
        row, column = (height + 1) // 2, 1 + (width - len(entry)) // 2
        self._generate_constraint((number, True, (row, column), entry))
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
            # We want the middle clue from the list of clues with an odd count.
            entry_length_clues = clues_by_size[entry_length]
            number, entry = entry_length_clues[len(entry_length_clues) // 2]
            self._generate_constraint((number, False, location, entry))

        for size, entries in clues_by_size.items():
            for index, (number1, entry1) in enumerate(entries[:len(entries) // 2]):
                number2, entry2 = entries[~index]
                locations = self._locations_for_size_down(size)
                for location1, location2 in locations:
                    ix1 = self._square_index(location1)
                    ix2 = self._square_index(location2)
                    # The index of the starting square must be at least as large as the
                    # clue number, and the difference between the starting squares must
                    # be at least as large as the difference between the clue numbers.
                    if ix1 < number1 or ix2 < number2 or ix2 - ix1 < number2 - number1:
                        continue
                    self._generate_constraint(
                        (number1, False, location1, entry1),
                        (number2, False, location2, entry2))


class FillInCrosswordGrid4Way (FillInCrosswordGridAbstract):
    acrosses: Sequence[int]
    downs: Sequence[int]

    def __init__(self, acrosses: Sequence[int],
                 downs: Sequence[int],
                 *, width: int):
        self.acrosses = acrosses
        self.downs = downs
        assert len(acrosses) == len(downs)
        assert acrosses == acrosses[::-1]
        assert Counter(acrosses) == Counter(downs)
        super().__init__(width=width, height=width)

    def get_grid_constraints(self, full):
        self.get_four_way_constraints()

    def get_four_way_constraints(self) -> None:
        width = self.width
        acrosses = self.acrosses
        downs = self.downs
        length = len(acrosses)
        down_by_size = defaultdict(list)
        for index, size in enumerate(downs):
            down_by_size[size].append(index)
        if len(self.acrosses) & 1 == 0:
            assert all(len(x) & 1 == 0 for x in down_by_size.values())
            if width & 1 == 0:
                row, column = width // 2, width + 1
            else:
                row, column = (width + 1) // 2, 1 + width // 2
        else:
            extra_size = acrosses[length // 2]
            assert len(down_by_size[extra_size]) & 1
            assert width & 1 == 1
            row, column = (width + 1) // 2, 1 + (width - extra_size) // 2
            number1 = length // 2
            number2 = (t := down_by_size[extra_size])[len(t) // 2]
            self._generate_constraint((number1, True, (row, column), extra_size),
                                      (number2, False, (column, row), extra_size))

        down_pairs_by_size = {size: [(indices[i], indices[~i]) for i in range(len(indices) // 2)]
                              for size, indices in down_by_size.items()}

        max_locations = {}
        for number, entry in list(enumerate(acrosses[:length // 2]))[::-1]:
            if column <= entry:
                row, column = row - 1, width + 1
            column -= entry
            max_locations[number] = (row, column)

        min_locations, row, column = {}, 1, 1
        for (number, entry) in enumerate(acrosses[:length // 2]):
            if column + entry > width + 1:
                row, column = row + 1, 1
            min_locations[number] = (row, column)
            column += entry

        for index, size in enumerate(acrosses[:length // 2]):
            assert acrosses[length - 1 - index] == size
            for row1, col1 in self._iterate_squares(
                    size, min_locations[index], max_locations[index]):
                row2, col2 = width + 1 - row1, width + 2 - col1 - size
                row3, col3 = col1, width + 1 - row1
                row4, col4 = col2, width + 1 - row2
                for (i3, i4) in down_pairs_by_size[size]:
                    self._generate_constraint((index, True, (row1, col1), size),
                                              (length - index - 1, True, (row2, col2), size),
                                              (i3, False, min((row3, col3), (row4, col4)), size),
                                              (i4, False, max((row3, col3), (row4, col4)), size))


    def handle_numbering(self) -> None:
        """
        Add constraints items to the clues to ensure that the numbering is in order.

        The clues are sorted by number, and then adjacent clues are looked at. If they
        are equal, (one being across, the other down), then we ensure they both go into
        the same location.  If they are not equal, we ensure that the first goes to a
        location prior to the second.
        """
        for is_across in (True, False):
            for index1, index2 in pairwise(range(len(self.acrosses))):
                locations = sorted(self.finder[index1, is_across] | self.finder[index2, is_across])
                locations_map = {location: index for index, location in enumerate(locations)}
                prefix = f'{index1}<{index2}{"da"[is_across]}'
                orderer = Orderer.LT(prefix, len(locations_map))
                self.optional_constraints.update(orderer.all_codes())
                for index, ordering in (index1, orderer.left), (index2, orderer.right):
                    for location, values in self.finder[index, is_across].items():
                        ordering_constraints = ordering(locations_map[location])
                        for value in values:
                            value.extend(ordering_constraints)

    @classmethod
    def _get_clue_name(cls, number, is_across):
        return chr(number + ord("A" if is_across else "a"))


class FillInCrosswordGridMushed (FillInCrosswordGridAbstract):
    clues: Sequence[tuple[int, str]]

    def __init__(self, clues: Sequence[tuple[int, str]],
                 *, width: Optional[int] = None, height: Optional[int] = None,
                 size: Optional[int] = None):
        self.clues = clues
        super().__init__(width=width, height=height, size=size)

    def get_grid_constraints(self, _full: bool) -> None:
        clues = self.clues
        clues_by_size = defaultdict(list)
        for (number, entry) in clues:
            clues_by_size[len(entry)].append((number, entry))

        self.handle_odd_size_counts(clues_by_size)
        self.handle_paired_entries(clues_by_size)

    def handle_paired_entries(self, clues_by_size: dict[int, list[tuple[int, str]]]):
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
                        # The index of the starting square must be at least as large as
                        # the clue number, and the difference between the starting squares
                        # must be at least as large as the difference between the clue
                        # numbers.
                        if ix1 < number1 or ix2 < number2 or ix2 - ix1 < number2 - number1:
                            continue
                        self._generate_constraint((number1, is_across, location1, entry1),
                                                  (number2, is_across, location2, entry2))

    def handle_odd_size_counts(self, clues_by_size: dict[int, list[tuple[int, str]]]):
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
                self._generate_constraint((number, is_across, location, entry),
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
                generate_centered_entry_for_size(odd_count, False,
                                                 (extra, 'MIDDLE-DOWN'))
                generate_centered_entry_for_size(odd_count, True,
                                                 (extra, 'MIDDLE-ACROSS'))

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
    results = filler.run(debug=0, black_squares_okay=False, numbering=True, full=False)
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
    results = filler.run(debug=0, black_squares_okay=False, full=False)
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
    results = filler.run(debug=0, black_squares_okay=False, numbering=True)
    for result in results:
        filler.display(result)


def test4():
    across_lengths = [6, 7, 4, 9, 10, 7, 4, 7, 5, 7, 5, 7, 5, 7, 4, 7, 10, 9, 4, 7, 6]
    down_lengths = [ 7, 9, 7, 7, 5, 4, 10, 4, 6, 7, 10, 5, 7, 9, 7, 7, 7, 6, 5, 4, 4]
    # across_lengths = across_lengths[1:-1]
    # down_lengths = [ 7, 9, 7, 7, 5, 4, 10, 4,  7, 10, 5, 7, 9, 7, 7, 7, 5, 4, 4]

    across_lengths = [6, 7, 4, 9, 10, 7, 4, 7, 5, 7,  7, 5, 7, 4, 7, 10, 9, 4, 7, 6]
    down_lengths = [ 7, 9, 7, 7, 5, 4, 10, 4, 6, 7, 10,  7, 9, 7, 7, 7, 6, 5, 4, 4]



    filler = FillInCrosswordGrid4Way(across_lengths, down_lengths, width=13)
    results = filler.run(debug=100, black_squares_okay=True, numbering=True)
    for result in results:
        filler.display(result)


if __name__ == '__main__':
    start = datetime.now()
    test1()
    test2()
    test3()
    test4()
    end = datetime.now()
    print("total time", end - start)

# 7.91   recursive=False
# 7.85   recursive=True
