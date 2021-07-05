import itertools
from typing import Sequence, Tuple

from cell import House
from feature import Feature
from features import KnightsMoveFeature, ThermometerFeature, SnakeFeature, \
    OddsAndEvensFeature, \
    SandwichFeature, KingsMoveFeature, \
    PalindromeFeature, XVFeature, NonConsecutiveFeature, KillerCageFeature, \
    LittleKillerFeature, KropkeDotFeature, ArrowFeature, BetweenLineFeature, ExtremesFeature
from grid import Grid
from human_sudoku import Sudoku
from draw_context import DrawContext
from quadruple_feature import QuadrupleFeature


class DrawCircleFeature(Feature):
    squares: Sequence[Tuple[int, int]]
    grid: Grid

    def initialize(self, grid: Grid) -> None:
        self.grid = grid

    def __init__(self, squares: Sequence[Tuple[int, int]]):
        self.squares = squares

    def draw(self, context: DrawContext) -> None:
        for row, column in self.squares:
            context.draw_circle((column + .5, row + .5), radius=.5, fill=False, color='blue')
        if all(self.grid.matrix[square].is_known for square in self.squares):
            value = ''.join(str(self.grid.matrix[square].known_value) for square in self.squares)
            print('Value =', value)
            context.draw_text(5.5, 0, value, fontsize=25, verticalalignment='center', horizontalalignment='center')


def puzzle_1(*, show: bool = False) -> None:
    puzzle = "...712.....7...3...5...8.471.8.....27.5.....19..1..4.5.2.4...6...3...7.....951..."
    feature = DrawCircleFeature([(1, 1), (1, 9), (3, 4), (4, 7), (5, 5), (6, 3), (7, 6), (9, 1), (9, 9)])
    Sudoku().solve(puzzle, features=(feature,), show=show)


def puzzle_2_366662343(*, show: bool = False) -> None:
    puzzle = "9...2...1.1.....2...2...3.......5...2.......5...3.......6...7...7.....8.5...7...6"
    features = [
        DrawCircleFeature([(1, 3), (2, 4), (3, 9), (4, 8), (5, 5), (6, 2), (7, 1), (8, 6), (9, 7)]),
        *NonConsecutiveFeature.setup()
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_3_799745399(*, show: bool = False) -> None:
    puzzle = "6...1...7.3.....2...1...5.....3.8...1.......2...1.2.....6...2...1.....4.4...2...3"
    features = [
        DrawCircleFeature([(1, 3), (1, 7), (3, 1), (3, 9), (5, 5), (7, 1), (7, 9), (9, 3), (9, 7)]),
        KnightsMoveFeature()
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_4_438953586(*, show: bool = False) -> None:
    puzzle = "...........51.23........1...1..5..2...........4..6..3...7........84.36..........."
    features = [
        DrawCircleFeature(list(itertools.product((1, 5, 9), (1, 5, 9)))),
        KingsMoveFeature()
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_5_192531473(*, show: bool = False) -> None:
    puzzle = '.6.-.5.1.72..3...3..8.--..8.3.---.4.9..--.1..4...1..25.3.5.-.7.'.replace('-', '...')
    features = [
        DrawCircleFeature([(2, 2), (2, 9), (3, 8), (4, 2), (5, 5), (6, 8), (7, 2), (8, 1), (8, 8)]),
        *SnakeFeature.disjoint_groups()
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_6_969231896(*, show: bool = False) -> None:
    puzzle = '1..3..5.9.2.---..4..6.6.2..7..---..8..6.5.8..6..---.4.2.7..5..3'.replace('-', '...')
    features = [
        DrawCircleFeature([(1, 6), (2, 1), (3, 7), (4, 9), (5, 5), (6, 1), (7, 3), (8, 9), (9, 4)]),
        SnakeFeature(((1, 3), (2, 3), (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (4, 3), (5, 3))),
        SnakeFeature(((5, 2), (6, 2), (7, 2), (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (9, 2))),
        SnakeFeature(((1, 8), (2, 5), (2, 6), (2, 7), (2, 8), (2, 9), (3, 8), (4, 8), (5, 8))),
        SnakeFeature(((5, 7), (6, 7), (7, 5), (7, 6), (7, 7), (7, 8), (7, 9), (8, 7), (9, 7))),
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_7_271479371(*, show: bool = False) -> None:
    puzzle = '4..-..3.1.2.3.4.------5...6...7------.8.9.1.2.3..-..5'.replace('-', '...')
    palindromes = ["3,1,SE,E", "3,2,E,SE", "3,4,E,SE", "3,6,SE,E", "3,7,E,SE",
                   "5,3,E,NE", "6,5,NE,E",
                   "7,1,NE,E", "7,2,E,NE", "7,4,E,NE", "7,6,NE,E", "7,7,E, NE"]
    features = [
        DrawCircleFeature([(1, 3), (1, 7), (2, 5), (5, 2), (5, 8), (8, 1), (8, 9), (9, 4), (9, 6)]),
        *[PalindromeFeature(descriptor, color="gray") for descriptor in palindromes],
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_8_867486467(*, show: bool = False) -> None:
    puzzle = '----,,123,-,,741.-..482.---.481..-.572..-.649..----'.replace('-', '...')
    features = [
        DrawCircleFeature([(1, 4), (1, 8), (2, 1), (4, 9), (5, 5), (6, 1), (8, 9), (9, 2), (9, 6)]),
        *(PalindromeFeature(((r, c), (r + 4, c + 4)), color='white') for r in (2, 3, 4) for c in (2, 3, 4)),
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_9_384937216(*, show: bool = False) -> None:
    grid = '2.O...O.1.e7e.e.o.O.e2o.o9O.o.6..1o...o.O.o...o3..1.o.O5o.o4e.O.o.e.e3e.3.O...O.4'
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.').replace('o', '.').replace('e', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']
    odds = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'o']
    evens = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'e']
    features = [
        DrawCircleFeature(circles),
        OddsAndEvensFeature(odds, evens)
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_10_561876789(*, show: bool = False) -> None:
    grid = '.O3...1O.1..9.2..8.2.O5O.7...4-5..6..4.5..3O.5...4.O.8..9..1.7..5O1..2.O1...8O.'
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.').replace('o', '.').replace('e', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']
    features = [
        DrawCircleFeature(circles),
        SnakeFeature.major_diagonal(),
        SnakeFeature.minor_diagonal(),
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_11_521327894(*, show: bool = False) -> None:
    grid = '-O.O-..9--O..-..O----.O.----O..-..O--2..-O.O-'
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']
    thermometers = ["1,3,W", "1,7,E,E,S,W", "2,6,S,S,E,N,N", "4,2,E,E,N,W,W", "6,8,W,W,S,E,E", "8,4,N,N,W,S,S",
                    "9,3,W,W,N,E", "9,7,E"]
    features = [
        DrawCircleFeature(circles),
        *[ThermometerFeature(thermometer) for thermometer in thermometers]
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_12_891914194(*, show: bool = False) -> None:
    grid = '-------.O.--O.O-..O.O.O..-O.O--.O--------'
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']
    features = [
        DrawCircleFeature(circles),
        KillerCageFeature(10, [(1, 1), (1, 2), (2, 1), (2, 2)]),
        KillerCageFeature(12, [(1, 3), (2, 3), (2, 4)]),
        KillerCageFeature(5, [(1, 4), (1, 5), ]),
        KillerCageFeature(18, [(1, 6), (1, 7), (2, 7)]),
        KillerCageFeature(30, [(1, 8), (1, 9), (2, 8), (2, 9)]),
        KillerCageFeature(15, [(2, 5), (2, 6)]),
        KillerCageFeature(16, Feature.parse_line("3,1,E,S")),
        KillerCageFeature(15, Feature.parse_line("3,4,W,S")),
        KillerCageFeature(14, Feature.parse_line("3,6,E,S")),
        KillerCageFeature(14, Feature.parse_line("3,8,E,S")),
        KillerCageFeature(13, Feature.parse_line("4,1,S")),
        KillerCageFeature(9, Feature.parse_line("4,8,S")),
        KillerCageFeature(12, Feature.parse_line("5,2,S")),
        KillerCageFeature(9, Feature.parse_line("5,9,S")),
        KillerCageFeature(22, Feature.parse_line("6,1,S,E")),
        KillerCageFeature(10, Feature.parse_line("6,3,S,E")),
        KillerCageFeature(17, Feature.parse_line("6,7,S,W")),
        KillerCageFeature(7, Feature.parse_line("6,8,S,E")),
        KillerCageFeature(17, Feature.parse_line("8,1,E,S,W")),
        KillerCageFeature(17, Feature.parse_line("8,3,S,E")),
        KillerCageFeature(8, Feature.parse_line("8,4,E")),
        KillerCageFeature(14, Feature.parse_line("8,6,E,S")),
        KillerCageFeature(21, Feature.parse_line("8,8,E,S,W")),
        KillerCageFeature(13, Feature.parse_line("9,5,E"))
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_13_535762978(*, show: bool = False) -> None:
    grid = 'O..-..O---..O-O..-.3.--.O.--.6.-..O-O..---O..-..O'
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']
    features = [
        DrawCircleFeature(circles),
        LittleKillerFeature(24, (3, 1), (-1, 1)),
        LittleKillerFeature(31, (5, 1), (-1, 1)),
        LittleKillerFeature(34, (7, 1), (-1, 1)),
        LittleKillerFeature(27, (3, 9), (1, -1)),
        LittleKillerFeature(15, (5, 9), (1, -1)),
        LittleKillerFeature(12, (7, 9), (1, -1)),

        LittleKillerFeature(61, (1, 3), (1, 1)),
        LittleKillerFeature(10, (1, 5), (1, 1)),
        LittleKillerFeature(6,  (1, 7), (1, 1)),

        LittleKillerFeature(8,  (9, 3), (-1, -1)),
        LittleKillerFeature(29, (9, 5), (-1, -1)),
        LittleKillerFeature(29, (9, 7), (-1, -1)),

    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_14_385478394(*, show: bool = False) -> None:
    grid = '1...O...O.2.--..3-O..-4..-O...5...O...O.6...O..-7..--.8...O.O...9'
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']
    print(circles)
    features = [
        *SandwichFeature.all(House.Type.COLUMN, [4, None, 18, None, 20, None, 19, None, 2]),
        *SandwichFeature.all(House.Type.ROW, [11, None, 10, None, 8, None, 32, None, 22]),
        DrawCircleFeature(circles),
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_15_436768313(*, show: bool = False) -> None:
    grid = '4..O....6----..O..O..O..7..4-.O.-2..1..O..O..O..----5..-O.1'
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']
    all_across = {5:  [(2, 5), (3, 2), (3, 7), (7, 2), (8, 5)],
                  10: [(2, 4), (7, 7), (8, 4)]}
    all_down = {5: [(6, 6), (7, 7)],
                10: [(2, 3), (2, 7), (3, 4), (4, 1), (5, 9), (7, 3)]}

    features = [
        DrawCircleFeature(circles),
        *XVFeature.setup(across=all_across, down=all_down, all_listed=False)
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_16_395396854(*, show: bool = False) -> None:
    grid = 'O..-O..-----..O-..1--.O...O-3..-O..-----..O.O...O'
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']
    features = [
        DrawCircleFeature(circles),
        *KropkeDotFeature.setup("3,1,N,E,N,E", color='white'),
        *KropkeDotFeature.setup("5,1,E,N,E,N,E,N,E,N", color='black'),
        *KropkeDotFeature.setup("6,3,N,E,N,E,N,E", color='white'),
        *KropkeDotFeature.setup("8,6,E,N,E,N", color='black'),
        *KropkeDotFeature.setup("9,8,N,E", color="white"),
        *KropkeDotFeature.setup("9,1,E", color="white"),
        *KropkeDotFeature.setup("1,8,E", color='black'),
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_17_272936289(*, show: bool = False) -> None:
    grid = '1....O..O--.O.---O..-..O..6--O..---.1.-.O.---O.O..6'
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']

    features = [
        DrawCircleFeature(circles),
        ArrowFeature("1,2,E,E"),
        ArrowFeature("3,7,SW,SW,SW"),
        ArrowFeature("4,4,NW,NW"),
        ArrowFeature("4,5,NW,NE,SE"),
        ArrowFeature("5,4,NW,SW,SE"),
        ArrowFeature("5,6,SE,NE,NW"),
        ArrowFeature("6,5,SE,SW,NW"),
        ArrowFeature("6,6,SE,SE"),
        ArrowFeature("8,9,N,N"),
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_18_725978489(*, show: bool = False) -> None:
    grid = "2....O3.O.3.-1O...4-.97O..1....O-.O.--..9-.O....6..3.O....7.67...O..8"
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']

    def createBetweenLines(row: int, column: int) -> Feature:
        squares = []
        while row <= 9 and column <= 9:
            squares.append((row, column))
            row, column = row + 1, column + 1
        return BetweenLineFeature(squares)

    features = [
        DrawCircleFeature(circles),
        createBetweenLines(5, 1),
        createBetweenLines(2, 1),
        createBetweenLines(1, 2),
        createBetweenLines(1, 3),
        createBetweenLines(1, 4),

    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_19_548565193(*, show: bool = False) -> None:
    grid = ".R.1O9.G.G.O.R.6.R.9.G.G.O.9.G...G.1OR..G..RO6.G...G.2.O.G.G.7.R.8.R.O.G.G.8O4.R."
    grid = grid.replace('-', '...')
    puzzle = grid.replace('O', '.')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']
    reds = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'R']
    greens = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'G']
    circles.append((5, 5))
    circles.sort()

    features = [
        *ExtremesFeature.setup(reds=reds, greens=greens),
        DrawCircleFeature(circles),
    ]
    Sudoku().solve(puzzle, features=features, show=show)


def puzzle_20_421265171(*, show: bool = False) -> None:
    grid = "..O-O..---O..-..O----.O.----O..-..O---..O..O-"
    grid = grid.replace('-', '...')
    circles = [(r, c) for (r, c), letter in zip(itertools.product(range(1, 10), repeat=2), grid) if letter == 'O']

    features = [
        DrawCircleFeature(circles),
        QuadrupleFeature(top_left=(1, 1), values=(5, 7, 9)),
        QuadrupleFeature(top_left=(1, 8), values=(1, 2, 3, 4)),
        QuadrupleFeature(top_left=(2, 2), values=(1, 3, 4)),
        QuadrupleFeature(top_left=(2, 4), values=(4, 5)),
        QuadrupleFeature(top_left=(3, 3), values=(7, 8, 9)),
        QuadrupleFeature(top_left=(3, 6), values=(1, 2, 3)),
        QuadrupleFeature(top_left=(4, 5), values=(4, 5, 6)),
        QuadrupleFeature(top_left=(4, 8), values=(1, 4)),
        QuadrupleFeature(top_left=(5, 1), values=(4, 5)),
        QuadrupleFeature(top_left=(5, 4), values=(7, 8, 9)),
        QuadrupleFeature(top_left=(6, 3), values=(1, 2, 3)),
        QuadrupleFeature(top_left=(6, 6), values=(4, 5, 7)),
        QuadrupleFeature(top_left=(7, 5), values=(3, 7)),
        QuadrupleFeature(top_left=(7, 7), values=(1, 8, 9)),
        QuadrupleFeature(top_left=(8, 1), values=(4, 7, 8, 9)),
        QuadrupleFeature(top_left=(8, 8), values=(2, 5, 6)),

    ]
    Sudoku().solve(' ' * 81, features=features, show=show)


def run() -> None:
    puzzles = [
         puzzle_1, puzzle_2_366662343, puzzle_3_799745399, puzzle_4_438953586, puzzle_5_192531473,
         puzzle_6_969231896, puzzle_7_271479371, puzzle_8_867486467, puzzle_9_384937216, puzzle_10_561876789,
         # puzzle_11_521327894, puzzle_12_891914194, puzzle_13_535762978, puzzle_14_385478394, puzzle_15_436768313,
         # puzzle_16_395396854, puzzle_17_272936289, puzzle_18_725978489, puzzle_19_548565193, puzzle_20_421265171
    ]
    # puzzles = [puzzle_20_421265171]
    for puzzle in puzzles:
        puzzle(show=False)


if __name__ == '__main__':
    run()
