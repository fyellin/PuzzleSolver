import itertools
import string
from collections import defaultdict
from functools import cache
from typing import NamedTuple

from solver import Clue as SClue, ConstraintSolver, DancingLinks, Encoder

ACROSS = [
    (1, "EPITAPHED"),
    (3, "OCA"),
    (6, "IRIDAL"),
    (7, "TRACTATOR"),
    (10, "CRU"),
    (11, "TEASET"),
    (13, "ACTIONMAN"),
    (14, "TYED", 3),
    (16, "BLAG", 3),
    (17, "TRIES", 3),
    (18, "ANADEMS"),
    (20, "SEZ"),
    (22, "ANGSTS"),
    (24, "ASP"),
    (26, "WEEVIL"),
    (28, "FIB"),
    (29, "REWRAP")
]

DOWN = [
    (2, "LATITAT"),
    (4, "CORN", 3),
    (5, "ARUM"),
    (8, "RENEWING"),
    (9, "SCABS"),
    (10, "CODE", 3),
    (12, "TALONS"),
    (13, "ADVERSE"),
    (15, "MAS", 3),
    (18, "ATEASE"),
    (19, "ASIF"),
    (21, "ZABRA"),
    (23, "LIETO"),
    (25, "PESHITTA"),
    (27, "PUPATE"),
    (30, "REDIA")
]


class Clue (NamedTuple):
    number: int
    is_across: bool
    word: str
    length: int
    special: bool = False

    @cache
    def name(self):
        return f'{self.number}{"a" if self.is_across else "d"}'


class AssymetricToroidalGrid:
    width: int
    height: int
    all_clues: list[Clue]
    min_locations: dict[int, tuple[int, int]]
    max_locations: dict[int, tuple[int, int]]

    def __init__(self, width, height, across=ACROSS, down=DOWN):
        self.width = width
        self.height = height
        all_clues = []
        for clues in (across, down):
            is_across = (clues == across)
            for number, word, *other in clues:
                if isinstance(word, int):
                    word, length = None, word
                else:
                    word, length = word, len(word)
                special = not not other
                if special:
                    length += 3
                clue = Clue(number, is_across, word, length, special)
                all_clues.append(clue)
        all_clues.sort(key=lambda clue: clue.number)
        self.all_clues = all_clues
        self.min_locations, self.max_locations = self.initialize_locations()

    def initialize_locations(self):
        across_clues = {clue.number: clue for clue in self.all_clues if clue.is_across}
        max_number = max(clue.number for clue in self.all_clues)

        min_locations = {}
        number = 1
        for row in range(1, self.height + 1):
            column = 1
            first_across = None  # if non-None, column of first across in row
            min_next_across = 0  # smallest column at which next across on this row can go
            while number <= max_number:
                if (clue := across_clues.get(number)) is None:
                    if column > self.width: break
                else:
                    column = max(column, min_next_across)
                    # If we're not the first across in the row, we can't wrap around
                    # to beyond where the first across began
                    if column + clue.length > self.width + (first_across or 1):
                        break
                    if first_across is None:
                        first_across = column
                    # Don't let the next across clue overlap this one.
                    min_next_across = column + clue.length
                min_locations[number] = (row, column)
                column, number = column + 1, number + 1

        max_locations = {}
        number = max_number
        for row in reversed(range(1, self.height + 1)):
            column = self.width
            previous_across = None  # if non-None, column of first across placed in row
            across_nogo = None      # if non-None, no across can be placed before here
            while number >= 1:
                if (clue := across_clues.get(number)) is None:
                    if column == 1: break
                else:
                    if previous_across is None:
                        # But this across right here, but the wrap-around area is unusable
                        across_nogo = max(1, column + clue.length - self.width)
                    else:
                        # We can't overlap the across already on the line
                        column = min(column, previous_across - clue.length)
                    if column < across_nogo: break
                    previous_across = column
                max_locations[number] = (row, column)
                column, number = column - 1, number - 1

        return min_locations, max_locations


    def create_constraints(self):
        encoder = Encoder(string.ascii_uppercase + '.')
        constraints = {}
        optional_constraints = set()
        for clue in self.all_clues:
            is_across = clue.is_across
            if not clue.word:
                continue
            if not clue.special:
                words = [clue.word]
            else:
                words = [clue.word[0:i] + '...' + clue.word[i:]
                         for i in range(0, len(clue.word) + 1)]
            for row, column in self.iterate_clue_start_location(clue):
                for word in words:
                    info = [clue.name()]
                    for char, location in zip(word,
                                              self.iterate_locations(row, column, is_across)):
                        info.extend(encoder.encode(char, location, is_across))
                    optional_constraints.update(info[1:])
                    constraints[clue.number, is_across, word, row, column] = info
        self.handle_numbering(constraints, optional_constraints)
        solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                              row_printer=self.my_printer)
        solver.solve(debug=False)

    def handle_numbering(self, constraints, optional_constraints) -> None:
        map = defaultdict(lambda: defaultdict(list))

        for key in constraints:
            number, is_across, word, row, column = key
            map[number, is_across][row, column].append(key)

        for clue1, clue2 in itertools.combinations(self.all_clues, 2):
            number1, number2 = clue1.number, clue2.number
            delta = number2 - number1
            # delta = deltas[number2] - deltas[number1]
            assert delta >= 0
            if delta > 0:
                def consistent(r1, c1, r2, c2):
                    return (r2 - r1) * self.width + (c2 - c1) >= delta
            else:
                def consistent(r1, c1, r2, c2):
                    return r1 == r2 and c1 == c2

            for location1, values1 in map[clue1.number, clue1.is_across].items():
                row1, column1 = location1
                item = f'{clue1.name()}@r{row1}c{column1}|{clue2.name()}'
                optional_constraints.add(item)
                for location2, values2 in map[clue2.number, clue2.is_across].items():
                    row2, column2 = location2
                    if not consistent(row1, column1, row2, column2):
                        item = item or f'{clue1.name()}@r{row1}c{column1}|{clue2.name()}'
                        for value in values2:
                            constraints[value].append(item)
                for value in values1:
                    constraints[value].append(item)

    def my_printer(self, solution):
        map = {(clue.number, clue.is_across) : clue for clue in self.all_clues}
        clues = []
        results = {}
        for (clue_number, is_across, word, row, column) in solution:
            clue = map[clue_number, is_across]
            length = clue.length
            locations = itertools.islice(self.iterate_locations(row, column, is_across), length)
            sclue = SClue(clue.name(), is_across, (row, column), length, locations=locations)
            clues.append(sclue)
            results[sclue] = word

        class MyEquationSolver(ConstraintSolver):
            def __init__(self):
                super().__init__(clues)

        MyEquationSolver().plot_board(results)

    def iterate_clue_start_location(self, clue):
        row, column = self.min_locations[clue.number]
        while (row, column) <= self.max_locations[clue.number]:
            yield row, column
            column += 1
            if column > self.width:
                row, column = row + 1, 1

    def iterate_locations(self, row, column, is_across):
        while True:
            yield row, column
            if is_across:
                column += 1
                if column > self.width:
                    column = 1
            else:
                row += 1
                if row > self.height:
                    row = 1


if __name__ == '__main__':
    x = AssymetricToroidalGrid(9, 13)
    x.create_constraints()

