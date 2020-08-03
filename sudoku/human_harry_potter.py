import datetime
import itertools
import math
from typing import Sequence, Tuple, List, Mapping, Iterable, Set, Optional

from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch

from cell import Cell, House
from grid import Grid
from human_sudoku import Sudoku
from human_features import Feature, KnightsMoveFeature, PossibilitiesFeature, MagicSquareFeature, \
    AdjacentRelationshipFeature, AllValuesPresentFeature, ThermometerFeature, SnakeFeature, LimitedValuesFeature, \
    SameValueAsExactlyOneMateFeature, SameValueAsAtLeastOneMateFeature, LittlePrincessFeature, \
    AlternativeBoxesFeature, SlowThermometerFeature, SandwichFeature, KingsMoveFeature, \
    QueensMoveFeature, SandwichXboxFeature
from skyscraper_feature import SkyscraperFeature


class MalvoloRingFeature(Feature):
    SQUARES = ((2, 4), (2, 5), (2, 6), (3, 7), (4, 8), (5, 8), (6, 8), (7, 7),
               (8, 6), (8, 5), (8, 4), (7, 3), (6, 2), (5, 2), (4, 2), (3, 3))

    class Adjacency(AdjacentRelationshipFeature):
        def __init__(self, squares: Sequence[Tuple[int, int]]) -> None:
            super().__init__("Malvolo Ring", squares, cyclic=True)

        def match(self, digit1: int, digit2: int) -> bool:
            return digit1 + digit2 in (4, 8, 9, 16)

    features: Sequence[Feature]
    special: Cell

    def __init__(self) -> None:
        self.features = [self.Adjacency(self.SQUARES), AllValuesPresentFeature(self.SQUARES)]

    def initialize(self, grid: Grid) -> None:
        self.special = grid.matrix[2, 4]
        for feature in self.features:
            feature.initialize(grid)

    def reset(self, grid: Grid) -> None:
        for feature in self.features:
            feature.reset(grid)

    def check(self) -> bool:
        return any(feature.check() for feature in self.features)

    def check_special(self) -> bool:
        """A temporary hack that it's not worth writing the full logic for.  If we set this value to 4,
           then it will start a cascade such that no variable on the ring can have a value of 2. """
        if len(self.special.possible_values) == 2:
            print("Danger, danger")
            self.special.set_value_to(2)
            return True
        return False

    def draw(self) -> None:
        radius = math.hypot(2.5, 1.5)
        plt.gca().add_patch(plt.Circle((5.5, 5.5), radius=radius, fill=False, facecolor='black'))


class GermanSnakeFeature(AdjacentRelationshipFeature):
    """A sequence of squares that must differ by 5 or more"""
    def __init__(self, name: str, snake:  Sequence[Tuple[int, int]]):
        super().__init__(name, snake)
        self.snake = snake

    def initialize(self, grid: Grid) -> None:
        super().initialize(grid)
        print("No Fives in a German Snake")
        Cell.remove_values_from_cells(self.cells, {5}, show=False)

    def match(self, digit1: int, digit2: int) -> bool:
        return abs(digit1 - digit2) >= 5


class ContainsTextFeature(PossibilitiesFeature):
    text: Sequence[int]

    """A row that must contain certain digits consecutively"""
    def __init__(self, row: int, text: Sequence[int]) -> None:
        super().__init__(f'Row {row}', [(row, column) for column in range(1, 10)])
        self.text = text

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        unused_digits = {digit for digit in range(1, 10) if digit not in self.text}
        text_template = [{v} for v in self.text]
        template = [unused_digits] * len(unused_digits)
        for text_position in range(0, len(unused_digits) + 1):
            line = (*template[0:text_position], *text_template, *template[text_position:])
            yield line


class LimitedKnightsMove(KnightsMoveFeature):
    BAD_INDICES = {(row, column) for row in (4, 5, 6) for column in (4, 5, 6)}

    def get_neighbors(self, cell: Cell) -> Iterable[Cell]:
        index = cell.index
        if index in self.BAD_INDICES:
            return
        for neighbor in super().get_neighbors(cell):
            if neighbor.index not in self.BAD_INDICES:
                yield neighbor


class SnakesEggFeature(Feature):
    """A snake egg, where eggs of size n have all the digits from 1-n"""

    class Egg(House):
        def __init__(self, index: int, cells: Sequence[Cell]) -> None:
            super().__init__(House.Type.EGG, index, cells)

        def reset(self) -> None:
            super().reset()
            self.unknown_values = set(range(1, len(self.cells) + 1))
            Cell.remove_values_from_cells(self.cells, set(range(len(self.cells) + 1, 10)))

    squares: Sequence[List[Tuple[int, int]]]

    def __init__(self, pattern: str) -> None:
        super().__init__()
        assert len(pattern) == 81
        info: Sequence[List[Tuple[int, int]]] = [list() for _ in range(10)]
        for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), pattern):
            if '0' <= letter <= '9':
                info[int(letter)].append((row, column))
        for i in range(0, 9):
            assert len(info[i]) == i
        self.squares = info

    def initialize(self, grid: Grid) -> None:
        eggs = [self.Egg(i, [grid.matrix[square] for square in self.squares[i]]) for i in range(1, 9)]
        grid.houses.extend(eggs)

    def draw(self) -> None:
        # Find all squares that aren't in one of the eggs.
        snake = set(itertools.product(range(1, 10), repeat=2))
        snake.difference_update(cell for size in range(1, 10) for cell in self.squares[size])
        self.draw_rectangles(snake, facecolor='lightblue')


class Pieces44(Feature):
    class Egg(House):
        def __init__(self, index: int, cells: Sequence[Cell]) -> None:
            super().__init__(House.Type.EGG, index, cells)

        def reset(self) -> None:
            super().reset()
            self.unknown_values = set(range(2, 10))
            Cell.remove_values_from_cells(self.cells, {1}, show=False)

    eggs: Sequence[List[Tuple[int, int]]]

    def __init__(self, pattern: str) -> None:
        super().__init__()
        assert len(pattern) == 81
        info: Sequence[List[Tuple[int, int]]] = [list() for _ in range(10)]
        for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), pattern):
            if '1' <= letter <= '7':
                info[int(letter)].append((row, column))
        for i in range(1, 8):
            assert len(info[i]) == 8
        self.eggs = info[1:8]

    def initialize(self, grid: Grid) -> None:
        eggs = [self.Egg(i + 1, [grid.matrix[square] for square in self.eggs[i]]) for i in range(len(self.eggs))]
        grid.houses.extend(eggs)

    def draw(self) -> None:
        colors = ('lightcoral', "violet", "bisque", "lightgreen", "lightgray", "yellow", "skyblue")
        for color, squares in zip(colors, self.eggs):
            self.draw_rectangles(squares, facecolor=color)


class PlusFeature(Feature):
    squares: Sequence[Tuple[int, int]]
    puzzles: Sequence[str]

    def __init__(self, squares: Sequence[Tuple[int, int]], puzzles: Sequence[str]) -> None:
        self.squares = squares
        self.puzzles = puzzles

    def reset(self, grid: Grid) -> None:
        for row, column in self.squares:
            value = self.__get_value(row, column)
            grid.matrix[row, column].set_value_to(value)

    def __get_value(self, row: int, column: int) -> int:
        index = (row - 1) * 9 + (column - 1)
        value = sum(int(puzzle[index]) for puzzle in self.puzzles) % 9
        if value == 0:
            value = 9
        return value

    def draw(self) -> None:
        for row, column in self.squares:
            plt.plot((column + .2, column + .8), (row + .5, row + .5), color='lightgrey', linewidth=3)
            plt.plot((column + .5, column + .5), (row + .2, row + .8), color='lightgrey', linewidth=3)


class ColorFeature(Feature):
    setup: Mapping[Tuple[int, int], str]
    color_map: Mapping[str, str]
    plus_feature: PlusFeature

    def __init__(self, grid: str, color_map: str, puzzles: Sequence[str]) -> None:
        super().__init__()
        self.setup = {(row, column): letter
                      for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), grid)
                      if letter != '.' and letter != '+'}
        pluses = [(row, column)
                  for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), grid)
                  if letter == '+']
        self.color_map = dict(zip(color_map, puzzles))
        self.plus_feature = PlusFeature(pluses, puzzles)

    def reset(self, grid: Grid) -> None:
        self.plus_feature.reset(grid)
        for (row, column), letter in self.setup.items():
            puzzle = self.color_map[letter]
            index = (row - 1) * 9 + (column - 1)
            value = int(puzzle[index])
            grid.matrix[row, column].set_value_to(value)

    CIRCLES = dict(r="lightcoral", p="violet", o="bisque", g="lightgreen", G="lightgray", y="yellow", b="skyblue")

    def draw(self) -> None:
        self.plus_feature.draw()
        axis = plt.gca()
        for (row, column), letter in self.setup.items():
            axis.add_patch(plt.Circle((column + .5, row + .5), radius=.4, fill=True,
                                      color=self.CIRCLES[letter]))
        # noinspection PyTypeChecker
        axis.add_patch(FancyBboxPatch((2.3, 5.3), 6.4, 0.4, boxstyle='round, pad=0.2', fill=False))


class DoubleSumFeature(PossibilitiesFeature):
    row_column: int
    htype: House.Type
    total: Optional[int]
    ptotal: int

    def __init__(self, htype: House.Type, row_column: int, ptotal: int, total: Optional[int] = None):
        name = f'DoubleSum {htype.name.title()} #{row_column}'
        squares = self.get_row_or_column(htype, row_column)
        self.row_column = row_column
        self.htype = htype
        self.total = total
        self.ptotal = ptotal
        super().__init__(name, squares, compressed=True)

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        total = self.total
        ptotal = self.ptotal
        for item1, item2 in itertools.permutations(range(1, 10), 2):
            if total and item1 + item2 != total:
                continue
            item3_possibilities = [item1] if item1 == 1 else [item2] if item1 == 2 \
                else [x for x in range(1, 10) if x not in {item1, item2}]
            for item3 in item3_possibilities:
                item4_possibilities = [item1] if item2 == 1 else [item2] if item2 == 2 \
                    else [x for x in range(1, 10) if x not in {item1, item2, item3}]
                item4 = ptotal - item3
                if item4 not in item4_possibilities:
                    continue
                other_values = set(range(1, 10)) - {item1, item2, item3, item4}
                temp = [{item1}, {item2}] + [other_values] * 7
                temp[item1 - 1] = {item3}
                temp[item2 - 1] = {item4}
                yield tuple(temp)

    def draw(self) -> None:
        args = {'fontsize': '15'}
        if self.total:
            self.draw_outside(f'{self.total}', self.htype, self.row_column, padding=.6, **args)
        self.draw_outside(f'{self.ptotal}', self.htype, self.row_column, **args)


class CageFeature(PossibilitiesFeature):
    total: int

    def __init__(self, total: int, squares: Sequence[Tuple[int, int]]):
        name = "Cage"
        self.total = total
        super().__init__(name, squares)

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        count = len(self.squares)
        for values in itertools.permutations(range(1, 10), count - 1):
            last_value = self.total - sum(values)
            if 1 <= last_value <= 9 and last_value not in values:
                result = (*values, last_value)
                yield CageFeature.fix_possibility(result)

    def draw(self) -> None:
        self.draw_outline(self.squares)
        row, column = min(self.squares)
        plt.text(column + .2, row + .2, str(self.total),
                 verticalalignment='top', horizontalalignment='left', fontsize=10, weight='bold')


class DrawBoxFeature(Feature):
    squares: Sequence[Tuple[int, int]]

    def __init__(self, squares: Sequence[Tuple[int, int]]):
        self.squares = squares

    def draw(self) -> None:
        self.draw_outline(self.squares)


def merge(p1: str, p2: str) -> str:
    assert len(p1) == len(p2) == 81
    assert(p1[i] == '.' or p2[i] == '.' or p1[i] == p2[i] for i in range(81))
    result = ((y if x == '.' else x) for x, y in zip(p1, p2))
    return ''.join(result)


def puzzle1() -> None:
    # XUZZ = "123456789123456789123456789123456789123456789123456789123456789123456789123456789"
    puzzle = "...6.1.....4...2...1.....6.1.......2....8....6.......4.7.....9...1...4.....1.2..3"
    texts = [(3, 1, 8), *[(x, 9) for x in range(1, 9)]]
    features: List[Feature] = [ContainsTextFeature(i, text) for i, text in enumerate(texts, start=1)]
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=features)


def puzzle2() -> None:
    previo = '...........................................5........3.............7..............'
    puzzle = '.9...16....................8............9............8....................16...8.'
    puzzle = merge(puzzle, previo)
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=[MalvoloRingFeature()])


def puzzle3() -> None:
    previo = '....4........6.............8.....9..........6.........2..........................'
    puzzle = '..9...7...5.....3.7.4.....9.............5.............5.....8.1.3.....9...7...5..'

    evens = [(2, 3), (3, 2), (3, 3), (1, 4), (1, 5), (1, 6)]
    evens = evens + [(column, 10 - row) for row, column in evens]
    evens = evens + [(10 - row, 10 - column) for row, column in evens]

    features = [SnakeFeature([(3, 6), (3, 5), (4, 4), (5, 4), (5, 5), (5, 6), (6, 6), (7, 5), (7, 4)]),
                LimitedValuesFeature(evens, (2, 4, 6, 8)),
                ]
    sudoku = Sudoku()
    sudoku.solve(merge(puzzle, previo), features=features)


def puzzle4() -> None:
    previo = '.......................1....4..................5...1.............................'
    puzzle = '...............5.....6.....' + (54 * '.')
    puzzle = merge(puzzle, previo)
    info1 = ((1, 2), (2, 2), (3, 3), (4, 4), (5, 4), (6, 4), (7, 4), (8, 4), (8, 3))
    info2 = tuple((row, 10-column) for (row, column) in info1)
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=[
        GermanSnakeFeature("Left", info1),
        GermanSnakeFeature("Right", info2), KnightsMoveFeature()
    ])


def puzzle5() -> None:
    previo = '..7......3.....5......................3..8............15.............9....9......'
    puzzle = '......3...1...............72.........................2..................8........'
    diadem = SnakeFeature([(4, 2), (2, 1), (3, 3), (1, 4), (3, 5), (1, 6), (3, 7), (2, 9), (4, 8)])
    thermometers = [ThermometerFeature(name, [(row, column) for row in (9, 8, 7, 6, 5, 4)])
                    for column in (2, 4, 6, 8)
                    for name in [f'Thermometer #{column // 2}']]
    features = [diadem, *thermometers]
    sudoku = Sudoku()
    sudoku.solve(merge(puzzle, previo), features=features)


def puzzle6() -> None:
    previo = '......................5....................6...1........2.................9......'
    puzzle = '......75.2.....4.9.....9.......2.8..5...............3........9...7......4........'
    snakey = '3...777773.5.77...3.5...22...555.....4...8888.4.6.8..8.4.6.88...4.6...1....666...'
    Sudoku().solve(merge(puzzle, previo), features=[SnakesEggFeature(snakey)])


def puzzle7() -> None:
    puzzles = [
        '925631847364578219718429365153964782249387156687215934472853691531796428896142573',   # Diary, Red
        '398541672517263894642987513865372941123894756974156238289435167456718329731629485',   # Ring, Purple
        '369248715152769438784531269843617952291854376675392184526973841438125697917486523',   # Locket, Orangeish
        '817325496396487521524691783741952638963148257285763149158279364632814975479536812',   # Cup, Yellow
        '527961384318742596694853217285619473473528169961437852152396748746285931839174625',   # Crown, Blue
        '196842753275361489384759126963125847548937261721684935612578394837496512459213678',   # Snake, Green
    ]
    pluses = [(1, 1), (1, 9), (2, 4), (2, 6), (3, 3), (3, 7), (4, 2), (4, 4), (4, 6), (4, 8), (5, 3)]
    pluses = pluses + [(10 - row, 10 - column) for row, column in pluses]
    puzzle = '......................7..1.....8.................6.....3..5......................'
    Sudoku().solve(puzzle, features=[(PlusFeature(pluses, puzzles))])


def puzzle8() -> None:
    puzzles = [
        '925631847364578219718429365153964782249387156687215934472853691531796428896142573',   # Diary, Red
        '398541672517263894642987513865372941123894756974156238289435167456718329731629485',   # Ring, Purple
        '369248715152769438784531269843617952291854376675392184526973841438125697917486523',   # Locket, Orangeish
        '817325496396487521524691783741952638963148257285763149158279364632814975479536812',   # Cup, Yellow
        '527961384318742596694853217285619473473528169961437852152396748746285931839174625',   # Crown, Blue
        '196842753275361489384759126963125847548937261721684935612578394837496512459213678',   # Snake, Green
        '213845679976123854548976213361782945859314762724569381632458197185297436497631528',   # Enigma, Gray
    ]

    grid = '+.y..o+.+...Gb.......p...r.+..+b.b+...........+g.g+..+.o...........ry...+.+g..g.+'
    features = [
        ColorFeature(grid, 'rpoybgG', puzzles),
        SnakeFeature.major_diagonal(),
        SnakeFeature.minor_diagonal(),
    ]
    Sudoku().solve('.'*81, features=features)


def magic_squares() -> None:
    puzzle = ('.' * 17) + "1" + ('.' * 54) + '.6.......'
    features = [
        MagicSquareFeature((2, 6)),
        MagicSquareFeature((4, 2)),
        MagicSquareFeature((6, 8)),
        MagicSquareFeature((8, 4)),
    ]
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=features)


def run_thermometer() -> None:
    thermometers = [[(2, 2), (1, 3), (1, 4), (1, 5), (2, 6)],
                    [(2, 2), (3, 1), (4, 1), (5, 1), (6, 2)],
                    [(2, 3), (2, 4), (2, 5), (3, 6), (3, 7), (4, 8)],
                    [(2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (6, 8)],
                    [(3, 2), (4, 3), (5, 4), (6, 5), (7, 6), (8, 7), (9, 7)],
                    [(4, 2), (5, 2), (6, 3), (7, 4), (8, 4)],
                    [(1, 7), (1, 8)],
                    [(8, 8), (8, 9)],
                    [(8, 2), (8, 3)]]
    puzzle = ' ' * 81
    features = [ThermometerFeature(f'Thermo {count}', thermometer)
                for count, thermometer in enumerate(thermometers, start=1)]
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=features)
    sudoku.draw_grid()


def thermo_magic() -> None:
    thermometers = [
        [(6 - r, 1) for r in range(1, 6)],
        [(6 - r, r) for r in range(1, 6)],
        [(1, 10 - r) for r in range(1, 6)],
        [(10 - r, 9) for r in range(1, 6)],
        [(10 - r, 4 + r) for r in range(1, 6)],
        [(9, 6 - r) for r in range(1, 6)]]
    features = [
        MagicSquareFeature(dr=4, dc=4, color='lightblue'),
        *[ThermometerFeature(f'Thermo #{count}', squares) for count, squares in enumerate(thermometers, start=1)]
    ]
    puzzle = ("." * 18) + '.....2...' + ('.' * 27) + '...8.....' + ('.' * 18)
    Sudoku().solve(puzzle, features=features)


def you_tuber() -> None:
    puzzle = '...........12986...3.....7..8.....2..1.....6..7.....4..9.....8...54823..........'
    features = [
        LimitedKnightsMove(),
        *[SameValueAsExactlyOneMateFeature((row, column)) for row in (4, 5, 6) for column in (4, 5, 6)]
    ]
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=features)


def little_princess() -> None:
    puzzle = '.......6...8..........27......6.8.1....4..........9..............7...............'
    Sudoku().solve(puzzle, features=[LittlePrincessFeature()])


def puzzle44() -> None:
    puzzle = "........8...........7............2................9....................5....36..."
    pieces = '1112.333.1.2223.33122.2233.111....44.5.64444..566.44..55.6677775556..77..566...77'
    Sudoku().solve(puzzle, features=[KnightsMoveFeature(), Pieces44(pieces)])


def puzzle_alice(*, show: bool = False) -> None:
    # puzzle = "......... 3......8. ..4...... ......... 2...9...7 ......... ......5.. .1......6 ........."
    puzzle = "......... 3....6.8. ..4...... ......... 2...9...7 ......... ......5.. .1......6 ........."  # 18:30

    pieces = "122222939112122333911123333441153666445555696497758966447958886447559886777778889"
    features = [AlternativeBoxesFeature(pieces),
                *(SameValueAsAtLeastOneMateFeature((r, c)) for r in range(1, 10) for c in range(1, 10))
                ]
    puzzle = puzzle.replace(' ', '')
    Sudoku().solve(puzzle, features=features, show=show)



def slow_thermometer_puzzle1() -> None:
    puzzle = '.' * 81
    thermos = [
        [(4, 5), (5, 5), (6, 6), (5, 6), (4, 6), (3, 7), (2, 7), (1, 6), (1, 5), (1, 4), (2, 3), (3, 3), (4, 4)],
        [(4, 5), (5, 5), (6, 6), (5, 7), (4, 7), (3, 8), (2, 8)],
        [(2, 2), (2, 1), (1, 1), (1, 2)],
        [(1, 7), (1, 8), (2, 9), (3, 9), (4, 8), (5, 8)],
        [(6, 4),  (5, 4),  (4, 3), (3, 2)],
        [(5, 3), (4, 2), (4, 1), (5, 2), (5, 1), (6, 1)],
        [(6, 8), (6, 9), (5, 9), (4, 9)],
        [(8, 4), (9, 3), (8, 2), (8, 3), (7, 4), (6, 3), (7, 3), (7, 2)],
        [(7, 6), (7, 7), (7, 8), (7, 9), (8, 8), (9, 8), (9, 7), (8, 6), (7, 5)]
    ]
    thermometers = [SlowThermometerFeature(f'Thermo#{i}', thermo)
                    for i, thermo in enumerate(thermos, start=1)]
    Sudoku().solve(puzzle, features=thermometers)


def slow_thermometer_puzzle2() -> None:
    puzzle = '.' * 72 + ".....1..."
    thermos = [
        "2,4,N,W,S,S,E,SE",
        "2,7,N,W,S",
        "4,6,N,NW",
        "4,7,N,SE,SE",
        "4,2,SW,E,SW,E,SW,E,SW,E,SW",
        "5,4,SE,E",
        "6,4,E,E",
        "7,3,S,S",
        "9,5,NW,S",
        "9,6,N",
        "9,6,NW",
        "6,7,E,SW,W,W,W,NW",
        "6,9,W,SW,W,W,W,NW",
        "8,8,NW",
        "8,8,W,SE,W"
    ]
    thermometers = [SlowThermometerFeature(f'Thermo#{i}', Feature.parse_line(line), color='lightblue')
                    for i, line in enumerate(thermos)]
    Sudoku().solve(puzzle, features=thermometers)


def thermometer_07_23() -> None:
    puzzle = ".....................9.............5...............3.................8.......9..."
    thermos = [
        "1,1,SE,SE,SE,SW,SW",
        "1,9,SW,SW,SW,NW,NW",
        "9,1,NE,NE,NE,SE,SE",
        "9,9,NW,NW,NW,NE,NE"
    ]
    thermometers = [ThermometerFeature(f'Thermo#{i}', Feature.parse_line(line), color='lightgray')
                    for i, line in enumerate(thermos)]
    Sudoku().solve(puzzle, features=thermometers)



def double_sum_puzzle(*, show: bool = False) -> None:

    class CheckSpecialFeature(Feature):
        cells: Sequence[Cell]

        def initialize(self, grid: Grid) -> None:
            self.cells = [grid.matrix[1, 6], grid.matrix[2, 6]]

        def check_special(self) -> bool:
            if len(self.cells[0].possible_values) == 4:
                print("Danger.  Danger")
                Cell.keep_values_for_cell(self.cells, {3, 7})
                return True
            return False

    features = [
        DoubleSumFeature(House.Type.ROW, 1, 6),
        DoubleSumFeature(House.Type.ROW, 4, 10, 10),
        DoubleSumFeature(House.Type.ROW, 5, 10, 9),
        DoubleSumFeature(House.Type.ROW, 6, 10, 10),
        DoubleSumFeature(House.Type.ROW, 7, 10, 10),
        DoubleSumFeature(House.Type.ROW, 9, 9, 11),

        DoubleSumFeature(House.Type.COLUMN, 1, 16),
        DoubleSumFeature(House.Type.COLUMN, 3, 13, 13),
        DoubleSumFeature(House.Type.COLUMN, 4, 12, 11),
        DoubleSumFeature(House.Type.COLUMN, 5, 9),
        DoubleSumFeature(House.Type.COLUMN, 6, 10, 10),
        DoubleSumFeature(House.Type.COLUMN, 7, 11, 15),
        DoubleSumFeature(House.Type.COLUMN, 8, 11, 9),

        CheckSpecialFeature(),
    ]
    Sudoku().solve('.' * 81, features=features, show=show)


def puzzle_hunt(*, show: bool = False) -> None:
    puzzle = "...48...7.8.5..6...9.....3.4...2.3..1...5...2..8..7......8.3.7...5...1.39...15.4."
    features = [SnakeFeature.major_diagonal(), SnakeFeature.minor_diagonal()]
    Sudoku().solve(puzzle, features=features, show=show)


def sandwich_07_28(*, show: bool = False) -> None:
    class LiarsSandwichFeature(SandwichFeature):
        def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
            yield from self._get_possibilities(self.total - 1)
            yield from self._get_possibilities(self.total + 1)

    puzzle = "..6................1...........1.....4.........9...2.....................7......8"
    features = [
        *[LiarsSandwichFeature(House.Type.ROW, row, total)
          for row, total in enumerate((5, 8, 5, 16, 12, 7, 5, 3, 1), start=1)],
        LiarsSandwichFeature(House.Type.COLUMN, 1, 5),
        LiarsSandwichFeature(House.Type.COLUMN, 5, 4),
        LiarsSandwichFeature(House.Type.COLUMN, 9, 5),
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def skyscraper_07_29(*, show: bool = False) -> None:
    basement = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (3, 1)]
    basement = basement + [(row, 10 - column) for row, column in basement]
    basement = basement + [(10 - row, column) for row, column in basement]

    features = [
        SkyscraperFeature(House.Type.ROW, 2, 2, None, basement=basement),
        SkyscraperFeature(House.Type.ROW, 3, None, 2, basement=basement),
        SkyscraperFeature(House.Type.ROW, 5, None, 5, basement=basement),
        SkyscraperFeature(House.Type.ROW, 6, 5, None, basement=basement),
        SkyscraperFeature(House.Type.ROW, 8, None, 5, basement=basement),
        SkyscraperFeature(House.Type.ROW, 9, 2, 2, basement=basement),

        SkyscraperFeature(House.Type.COLUMN, 2, 5, None, basement=basement),
        SkyscraperFeature(House.Type.COLUMN, 3, 2, None, basement=basement),
        SkyscraperFeature(House.Type.COLUMN, 4, 2, None, basement=basement),
        SkyscraperFeature(House.Type.COLUMN, 5, 5, 5, basement=basement),
        SkyscraperFeature(House.Type.COLUMN, 6, 2, 5, basement=basement),
        SkyscraperFeature(House.Type.COLUMN, 8, 5, None, basement=basement),
        SkyscraperFeature(House.Type.COLUMN, 9, 2, 2, basement=basement),
    ]

    Sudoku().solve('.' * 81, features=features, show=show)


def puzzle_07_30(*, show: bool = False) -> None:
    features = [
        SandwichXboxFeature(House.Type.ROW, 3, 16),
        SandwichXboxFeature(House.Type.ROW, 4, 10, right=True),
        SandwichXboxFeature(House.Type.COLUMN, 3, 30),
        SandwichXboxFeature(House.Type.COLUMN, 4, 3),
        SandwichXboxFeature(House.Type.COLUMN, 7, 17),
        KingsMoveFeature(),
        QueensMoveFeature(),
    ]
    puzzle = "." * 63 + '.5.......' + '.' * 9
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_07_30_Simon(*, show: bool = False) -> None:
    thermos = [
        "2,1,NE,S,NE,S,NE",
        "2,4,NE,S,NE,S,NE",
        "2,7,NE,S",
        "4,3,W,S,E,E,N",
        "4,7,W,S,E,E,N",
        "7,5,E,N,NW",
        "8,3,S,E,E,E",
        "9,8,N,E,N"
    ]
    thermometers = [ThermometerFeature(f'Thermo#{i}', Feature.parse_line(line), color='lightblue')
                    for i, line in enumerate(thermos, start=1)]
    nada = "........."
    puzzle = nada + "......3.." + nada * 6 + ".......3."
    Sudoku().solve(puzzle, features=thermometers, show=show)


if __name__ == '__main__':
    start = datetime.datetime.now()
    skyscraper_07_29()
    end = datetime.datetime.now()
    print(end - start)
