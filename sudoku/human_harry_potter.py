import datetime
import itertools
import math
from typing import Sequence, Tuple, List, Mapping, Iterable, Set, Optional

from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch

from cell import Cell, House, Egg
from grid import Grid
from human_sudoku import Sudoku, Feature, KnightsMoveFeature, MagicSquareFeature, PossibilitiesFeature, \
    AdjacentRelationshipFeature, AllDigitsFeature


class MalvoloRingFeature(Feature):
    SQUARES = ((2, 4), (2, 5), (2, 6), (3, 7), (4, 8), (5, 8), (6, 8), (7, 7),
               (8, 6), (8, 5), (8, 4), (7, 3), (6, 2), (5, 2), (4, 2), (3, 3))

    class Adjacency(AdjacentRelationshipFeature):
        def __init__(self, squares: Sequence[Tuple[int, int]]) -> None:
            super().__init__(squares, cyclic=True)

        def match(self, digit1: int, digit2: int) -> bool:
            return digit1 + digit2 in (4, 8, 9, 16)

    features: Sequence[Feature]
    special: Cell

    def __init__(self) -> None:
        self.features = [self.Adjacency(self.SQUARES), AllDigitsFeature(self.SQUARES)]

    def attach_to_board(self, sudoku: Sudoku) -> None:
        self.special = sudoku.grid.matrix[2, 6]
        for feature in self.features:
            feature.attach_to_board(sudoku)

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
        plt.gca().add_patch(plt.Circle((5.5, 5.5), radius=3, fill=False, facecolor='black'))


class GermanSnakeFeature(AdjacentRelationshipFeature):
    """A sequence of squares that must differ by 5 or more"""
    def __init__(self, snake:  Sequence[Tuple[int, int]]):
        super().__init__(snake)
        self.snake = snake

    def attach_to_board(self, sudoku: Sudoku) -> None:
        super().attach_to_board(sudoku)
        print("No Fives in a German Snake")
        Cell.remove_values_from_cells(self.cells, {5}, show=False)

    def match(self, digit1: int, digit2: int) -> bool:
        return abs(digit1 - digit2) >= 5


class ThermometerFeature(AdjacentRelationshipFeature):
    """
    A sequence of squares that must monotomically increase.
    This is implemented as a subclass of AdjacentRelationshipFeature.  Two implementations are provided, and we
    have to figure out which is better.
    """
    def __init__(self, thermometer: Sequence[Tuple[int, int]]) -> None:
        super().__init__(thermometer)
        self.thermometer = thermometer

    def attach_to_board(self, sudoku: Sudoku) -> None:
        super().attach_to_board(sudoku)

        length = len(self.cells)
        span = 10 - length  # number of values each element in thermometer can have
        for minimum, cell in enumerate(self.cells, start=1):
            maximum = minimum + span - 1
            bad_values = list(range(1, minimum)) + list(range(maximum + 1, 10))
            Cell.remove_values_from_cells([cell], set(bad_values))

    def match(self, digit1: int, digit2: int) -> bool:
        return digit1 < digit2

    def draw(self) -> None:
        self.draw_line(self.squares, color='lightgrey', linewidth=5)
        row, column = self.squares[0]
        plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor='lightgrey'))


class AltThermometerFeature(PossibilitiesFeature):
    """
    A sequence of squares that must monotonically increase.
    This is implemented as a subclass of Possibilities Feature.  Not sure which implementation is better.
    """
    def __init__(self, thermometer: Sequence[Tuple[int, int]]):
        super().__init__("Thermometer", thermometer, self.get_possibilities(len(thermometer)))

    def draw(self) -> None:
        self.draw_line(self.squares, color='lightgrey', linewidth=5)
        row, column = self.squares[0]
        plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor='lightgrey'))

    @classmethod
    def get_possibilities(cls, length: int) -> Iterable[Tuple[Set[int], ...]]:
        return cls.fix_possibilities(itertools.combinations(range(1, 10), length))

class AltAltThermometerFeature(PossibilitiesFeature):
    """
    A sequence of squares that must monotonically increase.
    This is implemented as a subclass of Possibilities Feature.  Not sure which implementation is better.
    """
    def __init__(self, thermometer: Sequence[Tuple[int, int]]):
        assert len(thermometer) >= 2
        super().__init__("Thermometer", thermometer, self.get_possibilities(len(thermometer)))

    def draw(self) -> None:
        self.draw_line(self.squares, color='lightgrey', linewidth=5)
        row, column = self.squares[0]
        plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor='lightgrey'))

    @classmethod
    def get_possibilities(cls, length: int) -> Iterable[Tuple[Set[int], ...]]:
        if length > 2:
            for permutation in itertools.combinations(range(2, 9), length - 2):
                yield (set(range(1, permutation[0])),
                       *cls.fix_possibility(permutation),
                       set(range(permutation[-1] + 1, 10)))
        else:
            for i in range(1, 9):
                yield {i}, set(range(1 + 1, 10))


class SnakeFeature(Feature):
    """A set of nine squares where each number is used exactly once."""
    squares: Sequence[Tuple[int, int]]
    cells: Sequence[Cell]

    def __init__(self, squares: Sequence[Tuple[int, int]]):
        self.squares = squares

    def get_houses(self, grid: Grid) -> Sequence[House]:
        cells = [grid.matrix[square] for square in self.squares]
        return [House(House.Type.EXTRA, 0, cells)]

    def check(self) -> bool:
        return False

    def draw(self) -> None:
        self.draw_line(self.squares, color='lightgrey', linewidth=5)
        row, column = self.squares[0]
        plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor='lightgrey'))


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


class LimitedValuesFeature(Feature):
    """A set of squares that can't contain all possible values"""
    squares: Sequence[Tuple[int, int]]
    values: Sequence[int]

    def __init__(self, squares: Sequence[Tuple[int, int]], values:Sequence[int]):
        self.squares = squares
        self.values = values

    def attach_to_board(self, sudoku: Sudoku) -> None:
        cells = [sudoku.grid.matrix[x] for x in self.squares]
        other_values = {i for i in range(1, 10) if i not in self.values}
        Cell.remove_values_from_cells(cells, other_values)

    def check(self) -> bool:
        pass


class SameValueAsOneOfFeature(Feature):
    main_square: Tuple[int, int]
    squares: Sequence[Tuple[int, int]]
    main_cell: Cell
    cells: Sequence[Cell]

    def __init__(self, main_square: Tuple[int, int], squares: Optional[Sequence[Tuple[int, int]]] = None):
        if squares is None:
            (r, c) = main_square
            squares = [(r + dr, c + dc) for dx in (-1, 1) for dy in (-2, 2)
                       for (dr, dc) in ((dx, dy), (dy, dx))
                       if 1 <= r + dr <= 8 and 1 <= c + dc <= 8]
        self.main_square = main_square
        self.squares = squares

    def attach_to_board(self, sudoku: Sudoku) -> None:
        self.main_cell = sudoku.grid.matrix[self.main_square]
        self.cells = [sudoku.grid.matrix[x] for x in self.squares]

    def check(self) -> bool:
        if self.main_cell.is_known:
            assert self.main_cell.known_value is not None
            return self.check_exactly_one_square_has_value(self.main_cell.known_value)
        else:
            return self.check_square_has_possible_value()

    def check_exactly_one_square_has_value(self, value: int) -> bool:
        count = sum(1 for cell in self.cells if cell.is_known and cell.known_value == value)
        mates = [cell for cell in self.cells if not cell.is_known and value in cell.possible_values]
        assert count < 2
        if count == 1:
            if mates:
                print(f'Cell {self.main_square} already has a mate')
                Cell.remove_value_from_cells(mates, value)
                return True
        elif len(mates) == 1:
            print(f'Cell {self.main_square} only has one possible mate')
            mates[0].set_value_to(value, show=True)
            return True
        return False

    def check_square_has_possible_value(self) -> bool:
        impossible_values = set()
        for value in self.main_cell.possible_values:
            count = sum(1 for cell in self.cells if cell.is_known and cell.known_value == value)
            mates = [cell for cell in self.cells if not cell.is_known and value in cell.possible_values]
            if count >= 2 or (count == 0 and not mates):
                impossible_values.add(value)
        if impossible_values:
            print(f'Cell {self.main_square} must have a matable value')
            Cell.remove_values_from_cells([self.main_cell], impossible_values)
            return True
        return False


class LimitedKnightsMove(KnightsMoveFeature):
    BAD_INDICES = {(row, column) for row in (4, 5, 6) for column in (4, 5, 6)}

    def is_neighbor(self, cell1: Cell, cell2: Cell) -> bool:
        if cell1.index in self.BAD_INDICES or cell2.index in self.BAD_INDICES:
            return False
        return super().is_neighbor(cell1, cell2)


class CheckEggFeature(Feature):
    """A snake egg, where eggs of size n have all the digits from 1-n"""
    squares: Sequence[List[Tuple[int, int]]]
    eggs: List[Egg]

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

    def get_houses(self, grid: Grid) -> Sequence[House]:
        self.eggs = [Egg(i, [grid.matrix[square] for square in self.squares[i]]) for i in range(1, 9)]
        return self.eggs

    def attach_to_board(self, sudoku: Sudoku) -> None:
        for egg in self.eggs:
            size = len(egg.cells)
            Cell.remove_values_from_cells(egg.cells, set(range(size + 1, 10)))

    def draw(self) -> None:
        cells = {cell for size in range(1, 10) for cell in self.squares[size]}
        for row, column in itertools.product(range(1, 10), repeat=2):
            if (row, column) not in cells:
                plt.gca().add_patch(plt.Rectangle((column, row), 1, 1, facecolor='lightblue'))


class PlusFeature(Feature):
    squares: Sequence[Tuple[int, int]]
    puzzles: Sequence[str]

    def __init__(self, squares: Sequence[Tuple[int, int]], puzzles: Sequence[str]) -> None:
        self.squares = squares
        self.puzzles = puzzles

    def attach_to_board(self, sudoku: Sudoku) -> None:
        for row, column in self.squares:
            value = self.__get_value(row, column)
            sudoku.grid.matrix[row, column].set_value_to(value)

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

    def attach_to_board(self, sudoku: Sudoku) -> None:
        self.plus_feature.attach_to_board(sudoku)
        for (row, column), letter in self.setup.items():
            puzzle = self.color_map[letter]
            index = (row - 1) * 9 + (column - 1)
            value = int(puzzle[index])
            sudoku.grid.matrix[row, column].set_value_to(value)

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
    sudoku.solve(puzzle, features=[GermanSnakeFeature(info1), GermanSnakeFeature(info2), KnightsMoveFeature()])


def puzzle5() -> None:
    previo = '..7......3.....5......................3..8............15.............9....9......'
    puzzle = '......3...1...............72.........................2..................8........'
    diadem = SnakeFeature([(4, 2), (2, 1), (3, 3), (1, 4), (3, 5), (1, 6), (3, 7), (2, 9), (4, 8)])
    thermometers = [ThermometerFeature([(row, column) for row in (9, 8, 7, 6, 5, 4)]) for column in (2, 4, 6, 8)]
    features = [diadem, *thermometers]
    sudoku = Sudoku()
    sudoku.solve(merge(puzzle, previo), features=features)


def puzzle6() -> None:
    previo = '......................5....................6...1........2.................9......'
    puzzle = '......75.2.....4.9.....9.......2.8..5...............3........9...7......4........'
    snakey = '3...777773.5.77...3.5...22...555.....4...8888.4.6.8..8.4.6.88...4.6...1....666...'
    Sudoku().solve(merge(puzzle, previo), features=[CheckEggFeature(snakey)])


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
    features = [ThermometerFeature(thermometer) for thermometer in thermometers]
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
        *[ThermometerFeature(squares) for squares in thermometers]
    ]
    puzzle = ("." * 18) + '.....2...' + ('.' * 27) + '...8.....' + ('.' * 18)
    Sudoku().solve(puzzle, features=features)


def you_tuber() -> None:
    puzzle = '...........12986...3.....7..8.....2..1.....6..7.....4..9.....8...54823..........'
    features = [
        LimitedKnightsMove(),
        *[SameValueAsOneOfFeature((row, column)) for row in (4, 5, 6) for column in (4, 5, 6)]
    ]
    sudoku = Sudoku()
    sudoku.solve(puzzle, features=features)


if __name__ == '__main__':
    ThermometerFeature = AltAltThermometerFeature
    start = datetime.datetime.now()
    thermo_magic()
    end = datetime.datetime.now()
    print(end - start)
