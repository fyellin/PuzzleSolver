from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from collections.abc import Hashable, Sequence, Callable, Iterable
from datetime import datetime
from enum import Enum
from functools import cache
from itertools import combinations, pairwise
from typing import Optional

from solver import Clue, DancingLinks, EquationSolver, Orderer

Square = tuple[int, int]

class SquareType(Enum):
    FILLED = 1
    CHECKED = 2
    ANY = 3
    BLANK = 4
    UNCHECKED = 5  # Across or Down, but not both.  Useful??

class FillInCrosswordGridAbstract(ABC):
    width: int
    height: int
    encoding: dict[str, tuple[tuple[int], tuple[int]]]
    constraints: dict[Hashable, list[str]]
    optional_constraints: set[str]
    results: list

    ACROSS_DOWN_NUMBERED_SEPARATELY = False

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

    def run(self, *, debug=0, numbering: bool = True, black_squares_okay: bool = False):
        time1 = datetime.now()

        self.constraints.clear()
        self.finder.clear()
        self.optional_constraints = {
            f'r{r}c{c}' for r in range(1, self.height + 1)
            for c in range(1, self.width + 1)}
        self.results.clear()

        try:
            self.get_grid_constraints()
            if numbering:
                self.handle_numbering()
            self.handle_black_squares(black_squares_okay)
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

    @abstractmethod
    def get_grid_constraints(self): ...

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
        sorted_finder_keys = sorted(self.finder.keys())
        if not self.ACROSS_DOWN_NUMBERED_SEPARATELY:
            clue_lists = [sorted_finder_keys]
        else:
            clue_lists = [
                [(n, True) for n, is_across in sorted_finder_keys if is_across],
                [(n, False) for n, is_across in sorted_finder_keys if not is_across]
            ]

        for clues in clue_lists:
            for clue1, clue2 in pairwise(clues):
                (number1, is_across1), (number2, is_across2) = clue1, clue2
                locations = sorted(self.finder[clue1].keys() | self.finder[clue2].keys())
                locations_map = {location: index
                                 for index, location in enumerate(locations)}
                assert number1 <= number2
                orderer_type, symbol = (
                    (Orderer.LT, '<') if number1 < number2 else (Orderer.EQ, '='))
                prefix = f'{number1}{'da'[is_across1]}{symbol}{number2}{'da'[is_across2]}'
                orderer = orderer_type(prefix, len(locations_map))
                self.optional_constraints.update(orderer.all_codes())
                for clue, ordering in ((clue1, orderer.left), (clue2, orderer.right)):
                    for location, values in self.finder[clue].items():
                        ordering_constraints = ordering(locations_map[location])
                        for value in values:
                            value.extend(ordering_constraints)

    def is_legal_pair_index(self, number1, location1: Square, number2,
                            location2: Square) -> bool:
        (row1, column1) = location1
        (row2, column2) = location2
        ix1 = (row1 - 1) * self.width + column1
        ix2 = (row2 - 1) * self.width + column2
        # The index of the starting square must be at least as large as the
        # clue number, and the difference between the starting squares must
        # be at least as large as the difference between the clue numbers.
        return ix1 >= number1 and ix2 >= number2 and ix2 - ix1 >= number2 - number1

    @cache
    def _locations_for_size_across(self, size: int):
        height, width = self.height, self.width
        result = []

        for row1 in range(1, height + 1):
            row2 = height + 1 - row1
            if row1 > row2:
                break
            for column1 in range(1, width + 2 - size):
                column2 = width + 2 - size - column1
                if (row1, column1 + size) <= (row2, column2):
                    result.append(((row1, column1), (row2, column2)))
        return result

    @cache
    def _locations_for_size_down(self, size: int) -> Sequence[tuple[Square, Square]]:
        height, width = self.height, self.width
        result = []
        for row1 in range(1, height + 2 - size):
            row2 = height + 2 - size - row1
            if row1 > row2:
                break
            for column1 in range(1, width + 1):
                column2 = width + 1 - column1
                if (row1, column1) < (row2, column2):
                    if column1 != column2 or row2 >= row1 + size:
                        result.append(((row1, column1), (row2, column2)))
        return result

    def handle_black_squares(self, black_squares_function: bool | Callable[[Square],
                             SquareType]) -> None:
        """
        If it's okay for a square to be empty, we just make it's rRcC-a and rRcC-d fields
        be optional.

        If we require a square to be filled either by across or down, but not by both,
        we handle it as shown by "At-Least-One-rRcC" below, which lets us make at most
        one of rRcC-a and rRcC-d optional, but not both.

        If we require a field to be a checked square (not handled yet), we do nothing.

        For now, we only handle all or nothing. But we can make it per square if we
        want.  In particular, we might let the center square be empty, but require
        everything else to be full.
        """
        if black_squares_function is True:
            black_squares_function = lambda r, c: SquareType.ANY
        elif black_squares_function is False:
            black_squares_function = lambda r, c: SquareType.FILLED

        for row in range(1, self.height + 1):
            for column in range(1, self.width + 1):
                t = f'r{row}c{column}'
                match square_type := black_squares_function(row, column):
                    case SquareType.FILLED | SquareType.UNCHECKED:
                        provider = f"At-Least-One-{t}"
                        self.constraints[f'At-Least-One-{t}-a'] = [provider, f'{t}-a']
                        self.constraints[f'At-Least-One-{t}-d'] = [provider, f'{t}-d']
                        if square_type == SquareType.FILLED:
                            # for an unchecked square, we *must* use one of the above
                            # constraints. For a filled square, we can use one or none
                            # of the above constraints (if the clue is checked.)
                            self.optional_constraints.add(provider)
                    case SquareType.ANY:
                        self.optional_constraints |= {f"{t}-a", f"{t}-d"}
                    case SquareType.CHECKED:
                        # My default f'{t}-a' and f'{t}-d' are both required, so the
                        # square will end up being double clued.
                        pass
                    case SquareType.BLANK:
                        # Create a new unique constraint that doesn't allow
                        self.constraints[f'{t}-blank'] = ['{t}-blank', f'{t}-d', f'{t}-a']

    def _generate_constraint(self,
                             *clue_location_entry: tuple[int, bool, Square, str | int],
                             extras: Sequence[str] = ()) -> None:
        name = tuple(self._get_clue(number, entry, base_location, is_across)
                     for number, is_across, base_location, entry in clue_location_entry)
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

    @staticmethod
    def inward_pairs(array):
        for i in range(len(array) // 2):
            yield array[i], array[~i]

    class MyClue(Clue):
        def __str__(self):
            r, c = self.base_location
            return f"<{self.name}@r{r}c{c}>"

    @classmethod
    @cache
    def _get_clue(cls, number, entry, base_location, is_across):
        clue_name = cls._get_clue_name(number, is_across)
        if isinstance(entry, str):
            length, context = len(entry), entry
        else:
            length, context = entry, None
        return cls.MyClue(clue_name, is_across, base_location, length, context=context)

    @classmethod
    def _get_clue_name(cls, number, is_across):
        return f'{number}{"DA"[is_across]}'


class FillInCrosswordGrid (FillInCrosswordGridAbstract):
    acrosses: Sequence[tuple[int, str]]
    downs: Sequence[tuple[int, str]]

    def __init__(self, acrosses: Sequence[tuple[int, str | int]],
                 downs: Sequence[tuple[int, str | int]],
                 *, width: Optional[int] = None, height: Optional[int] = None,
                 size: Optional[int] = None):
        self.acrosses = acrosses
        self.downs = downs
        super().__init__(width=width, height=height, size=size)

    def get_grid_constraints(self):
        self.get_across_constraints()
        self.get_down_constraints()

    def get_across_constraints(self) -> None:
        acrosses, width, height = self.acrosses, self.width, self.height
        clue_count = len(acrosses)
        if (clue_count & 1) == 1:
            number, entry = acrosses[clue_count // 2]
            assert height & 1 == 1  # must be odd height
            length = entry if isinstance(entry, int) else len(entry)
            assert (width - length) & 1 == 0  # width and central entry have same parity
            # Set row, column to the starting location of this entry
            row, column = (height + 1) // 2, 1 + (width - length) // 2
            self._generate_constraint((number, True, (row, column), entry))
        else:
            # Set row, column to the square just beyond the first half of the
            # grid.  This is just beyond where the last letter of the first half of
            # the clues can go.
            if height & 1 == 0:
                row, column = height // 2, width + 1
            else:
                row, column = (height + 1) // 2, 1 + width // 2

        max_locations = {}
        for number, entry in reversed(acrosses[:clue_count // 2]):
            length = entry if isinstance(entry, int) else len(entry)
            if column <= length:
                row, column = row - 1, width + 1
            column -= length
            max_locations[number] = (row, column)

        min_locations, row, column = {}, 1, 1
        for (number, entry) in acrosses[:clue_count // 2]:
            length = entry if isinstance(entry, int) else len(entry)
            if column + length > width + 1:
                row, column = row + 1, 1
            min_locations[number] = (row, column)
            column += length

        for (number1, entry1), (number2, entry2) in self.inward_pairs(acrosses):
            length1 = entry1 if isinstance(entry1, int) else len(entry1)
            length2 = entry2 if isinstance(entry2, int) else len(entry2)
            assert length1 == length2
            for row1, col1 in self._iterate_squares(
                    length1, min_locations[number1], max_locations[number1]):
                row2, col2 = height + 1 - row1, width + 2 - col1 - length1
                self._generate_constraint((number1, True, (row1, col1), entry1),
                                          (number2, True, (row2, col2), entry2))

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
            for (number1, entry1), (number2, entry2) in self.inward_pairs(entries):
                locations = self._locations_for_size_down(size)
                for location1, location2 in locations:
                    if self.is_legal_pair_index(number1, location1, number2, location2):
                        self._generate_constraint(
                            (number1, False, location1, entry1),
                            (number2, False, location2, entry2))

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


class FillInCrosswordGrid4Way (FillInCrosswordGrid):

    ACROSS_DOWN_NUMBERED_SEPARATELY = True

    def __init__(self, acrosses: Sequence[int | str], downs: Sequence[int | str],
                 *, width: int):
        assert len(acrosses) == len(downs), "Acrosses and Downs must have the same length"
        across_length = [x if isinstance(x, int) else len(x) for x in acrosses]
        down_length = [x if isinstance(x, int) else len(x) for x in downs]
        assert across_length == across_length[::-1], "Across lengths must be a palindrome"
        assert Counter(across_length) == Counter(down_length), "Acrosses and Downs must have the same count of each clue size"
        super().__init__(list(enumerate(acrosses, start=1)),
                         list(enumerate(downs, start=1)), size=width)
        self.down_by_size = defaultdict(list)
        for number, entry in self.downs:
            self.down_by_size[entry].append((number, entry))

    def get_grid_constraints(self):
        self.get_across_constraints()

    def _generate_constraint(self,
                             *clue_location_entry: tuple[int, bool, Square, str | int],
                             extras: Sequence[str] = ()) -> None:
        assert 1 <= len(clue_location_entry) <= 2
        if len(clue_location_entry) == 1:
            number1, is_across, (row, column), value = clue_location_entry[0]
            length = value if isinstance(value, int) else len(value)
            assert len(self.down_by_size[length]) & 1 == 1
            number2, value2 = (t := self.down_by_size[length])[len(t) // 2]
            super()._generate_constraint(clue_location_entry[0],
                                         (number2, False, (column, row), value2),
                                         extras=extras)
        else:
            number1, is_across1, (row1, col1), value1 = clue_location_entry[0]
            number2, is_across2, (row2, col2), value2 = clue_location_entry[1]
            assert is_across1 and is_across2
            length = value1 if isinstance(value1, int) else len(value1)
            location3 = col1, self.width + 1 - row1  # row1, col1 rotated 90º
            location4 = col2, self.width + 1 - row2  # row2, col2 rotated 90º
            # location3 and location4 may be out of order. If so, fix.
            if location3 > location4:
                location3, location4 = location4, location3
            downs = self.down_by_size[length]
            for (number3, value3), (number4, value4) in self.inward_pairs(downs):
                if self.is_legal_pair_index(number3, location3, number4, location4):
                    super()._generate_constraint(
                        *clue_location_entry,

       (number3, False, location3, value3),
                        (number4, False, location4, value4), extras=extras)

    @classmethod
    def _get_clue_name(cls, number, is_across):
        return chr(number - 1 + ord("A" if is_across else "a"))


class FillInCrosswordGridMushed (FillInCrosswordGridAbstract):
    clues: Sequence[tuple[int, str]]

    def __init__(self, clues: Sequence[tuple[int, str]],
                 *, width: Optional[int] = None, height: Optional[int] = None,
                 size: Optional[int] = None):
        self.clues = clues
        super().__init__(width=width, height=height, size=size)

    def get_grid_constraints(self) -> None:
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
                        # The index of the starting square must be at least as large as
                        # the clue number, and the difference between the starting squares
                        # must be at least as large as the difference between the clue
                        # numbers.
                        if self.is_legal_pair_index(number1, location1, number2, location2):
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
    results = filler.run(debug=5, numbering=True, black_squares_okay=False)
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
    results = filler.run(debug=5, black_squares_okay=False)
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
    results = filler.run(debug=5, numbering=True, black_squares_okay=False)
    for result in results:
        filler.display(result)


def test4():
    across_lengths = [6, "abcdefg", 4, 9, 10, 7, 4, 7, 5, 7, 5, 7, 5, 7, 4, 7, 10, 9, 4, 7, 6]
    down_lengths = [ 7, 9, 7, 7, 5, 4, 10, 4, 6, 7, 10, 5, 7, 9, 7, 7, 7, 6, 5, 4, 4]
    across_lengths = across_lengths[1:-1]
    down_lengths = [ 7, 9, 7, 7, 5, 4, 10, 4,  7, 10, 5, 7, 9, 7, 7, 7, 5, 4, 4]

    # across_lengths = [6, 7, 4, 9, 10, 7, 4, 7, 5, 7,  7, 5, 7, 4, 7, 10, 9, 4, 7, 6]
    #  down_lengths = [ 7, 9, 7, 7, 5, 4, 10, 4, 6, 7, 10,  7, 9, 7, 7, 7, 6, 5, 4, 4]

    filler = FillInCrosswordGrid4Way(across_lengths, down_lengths, width=13)
    results = filler.run(debug=100, numbering=True, black_squares_okay=True)
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
