import datetime
import itertools
import math
from typing import Sequence, Tuple, List, Mapping, Iterable, Set

from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch

from cell import Cell, House
from grid import Grid
from human_sudoku import Sudoku
from human_features import Feature, KnightsMoveFeature, PossibilitiesFeature, MagicSquareFeature, \
    AdjacentRelationshipFeature, AllValuesPresentFeature, ThermometerFeature, SnakeFeature, LimitedValuesFeature, \
    SameValueAsExactlyOneMateFeature, SameValueAsAtLeastOneMateFeature, LittlePrincessFeature, AlternativeBoxesFeature


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
        print("No Fives in a German Snake")
        Cell.remove_values_from_cells(self.cells, {5}, show=False)

    def match(self, digit1: int, digit2: int) -> bool:
        return abs(digit1 - digit2) >= 5


class ContainsTextFeature(PossibilitiesFeature):
    """A row that must contain certain digits consecutively"""
    def __init__(self, row: int, text: Sequence[int]) -> None:
        super().__init__(f'Row {row}', [(row, column) for column in range(1, 10)], self.get_possibilities(text))

    @staticmethod
    def get_possibilities(text: Sequence[int]) -> Iterable[Tuple[Set[int], ...]]:
        unused_digits = {digit for digit in range(1, 10) if digit not in text}
        text_template = [{v} for v in text]
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
        cells = {cell for size in range(1, 10) for cell in self.squares[size]}
        for row, column in itertools.product(range(1, 10), repeat=2):
            if (row, column) not in cells:
                plt.gca().add_patch(plt.Rectangle((column, row), 1, 1, facecolor='lightblue'))


class Pieces44(Feature):
    class Egg(House):
        def __init__(self, index: int, cells: Sequence[Cell]) -> None:
            super().__init__(House.Type.EGG, index, cells)

        def reset(self) -> None:
            super().reset()
            self.unknown_values = set(range(2, 10))
            Cell.remove_values_from_cells(self.cells, {1}, show=False)

    squares: Sequence[List[Tuple[int, int]]]

    def __init__(self, pattern: str) -> None:
        super().__init__()
        assert len(pattern) == 81
        info: Sequence[List[Tuple[int, int]]] = [list() for _ in range(10)]
        for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), pattern):
            if '1' <= letter <= '7':
                info[int(letter)].append((row, column))
        for i in range(1, 8):
            assert len(info[i]) == 8
        self.squares = info[1:8]

    def initialize(self, grid: Grid) -> None:
        eggs = [self.Egg(i + 1, [grid.matrix[square] for square in self.squares[i]]) for i in range(len(self.squares))]
        grid.houses.extend(eggs)

    def draw(self) -> None:
        colors = ('lightcoral', "violet", "bisque", "lightgreen", "lightgray", "yellow", "skyblue")
        for color, squarex in zip(colors, self.squares):
            for row, column in squarex:
                plt.gca().add_patch(plt.Rectangle((column, row), 1, 1, facecolor=color))


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
        SnakeFeature([(i, i) for i in range(1, 10)]),
        SnakeFeature([(10 - i, i) for i in range(1, 10)]),
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


def puzzle_alice() -> None:
    # puzzle = "......... 3......8. ..4...... ......... 2...9...7 ......... ......5.. .1......6 ........."
    puzzle = "......... 3....6.8. ..4...... ......... 2...9...7 ......... ......5.. .1......6 ........." #18:30

    pieces = "122222939112122333911123333441153666445555696497758966447958886447559886777778889"
    features = [AlternativeBoxesFeature(pieces),
                *(SameValueAsAtLeastOneMateFeature((r, c)) for r in range(1, 10) for c in range(1, 10))
                ]
    puzzle = puzzle.replace(' ', '')
    Sudoku().solve(puzzle, features=features)


if __name__ == '__main__':
    start = datetime.datetime.now()
    puzzle_alice()
    end = datetime.datetime.now()
    print(end - start)

