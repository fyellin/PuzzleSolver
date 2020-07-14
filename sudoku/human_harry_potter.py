import itertools
from typing import Sequence, Tuple, Iterator, Optional, List, Mapping

from matplotlib import pyplot as plt
from matplotlib.patches import FancyBboxPatch

from cell import Cell, House, Egg
from grid import Grid
from human_sudoku import Sudoku, Feature, KnightsMoveFeature


class GermanSnakeFeature(Feature):
    GERMAN_SNAKE_INFO = {1: {6, 7, 8, 9}, 2: {7, 8, 9}, 3: {8, 9}, 4: {9},
                         6: {1}, 7: {1, 2}, 8: {1, 2, 3}, 9: {1, 2, 3, 4}}

    snake: Sequence[Tuple[int, int]]
    snake_cells: Sequence[Cell]

    def __init__(self, snake:  Sequence[Tuple[int, int]]):
        self.snake = snake

    def start_checking(self, sudoku: Sudoku):
        self.snake_cells = [sudoku.grid.matrix[location] for location in self.snake]
        print("No Fives in a German Snake")
        fives = [cell for cell in self.snake_cells if 5 in cell.possible_values]
        Cell.remove_value_from_cells(fives, 5)

    def check(self, sudoku: Sudoku) -> bool:
        previous_cells: Iterator[Optional[Cell]] = itertools.chain([None], self.snake_cells)
        next_cells: Iterator[Optional[Cell]] = itertools.chain(
            itertools.islice(self.snake_cells, 1, None), [None])

        for cell, previous, nexxt in zip(self.snake_cells, previous_cells, next_cells):
            impossible_values = set()
            for value in cell.possible_values:
                prev_bridge = self.get_bridge(cell, previous, value)
                next_bridge = self.get_bridge(cell, nexxt, value)
                if not prev_bridge or not next_bridge:
                    impossible_values.add(value)
                elif previous and nexxt and previous.is_neighbor(nexxt) and len(prev_bridge.union(next_bridge)) == 1:
                    impossible_values.add(value)

            if impossible_values:
                print("No appropriate value in adjacent cell")
                Cell.remove_values_from_cells([cell], impossible_values)
                return True
        return False

    def draw(self, _sudoku: Sudoku) -> None:
        xs = [column + .5 for _, column in self.snake]
        ys = [row + .5 for row, _ in self.snake]
        plt.plot(xs, ys, color='gold', linewidth=5)

    def get_bridge(self, cell: Cell, adjacent: Optional[Cell], value: int):
        good_adjacent_values = self.GERMAN_SNAKE_INFO[value]
        if not adjacent:
            return good_adjacent_values
        bridge = adjacent.possible_values.intersection(good_adjacent_values)
        if cell.is_neighbor(adjacent) and value in bridge:
            bridge.discard(value)
        return bridge


class MalvoloRingFeature(Feature):
    MARVOLO_RING_INFO = {1: (3, 7, 8), 2: {2, 6, 7}, 3: {1, 5, 6}, 4: {4, 5}, 5: {3, 4}, 6: {2, 3}, 7: {1, 2, 9},
                         8: {1, 8}, 9: {7}}
    ring_cells: Sequence[Cell]

    def start_checking(self, sudoku: Sudoku):
        self.ring_cells = [sudoku.grid.matrix[x] for x in (
            (2, 4), (2, 5), (2, 6), (3, 7), (4, 8), (5, 8), (6, 8), (7, 7),
            (8, 6), (8, 5), (8, 4), (7, 3), (6, 2), (5, 2), (4, 2), (3, 3))]

    def check(self, sudoku: Sudoku) -> bool:
        for index, cell in enumerate(self.ring_cells):
            if cell.is_known:
                continue
            impossible_values = set()
            adjacent1, adjacent2 = (self.ring_cells[(index - 1) % 16], self.ring_cells[(index + 1) % 16])
            for value in cell.possible_values:
                bridge1, bridge2 = self.get_bridge(cell, adjacent1, value), self.get_bridge(cell, adjacent2, value)
                if not bridge1 or not bridge2:
                    impossible_values.add(value)
                elif adjacent1.is_neighbor(adjacent2) and len(bridge1.union(bridge2)) == 1:
                    # You can't use the same value on both sides if it is a neighbor to both
                    impossible_values.add(value)

            if impossible_values:
                print("No appropriate value in adjacent cells")
                Cell.remove_values_from_cells([cell], impossible_values)
                return True

        known_cell_values = {cell.known_value for cell in self.ring_cells if cell.is_known}
        unknown_cell_values = [value for value in range(1, 10)if value not in known_cell_values]
        unknown_cells = {cell for cell in self.ring_cells if not cell.is_known}
        result = False
        for value in unknown_cell_values:
            cells = [cell for cell in unknown_cells if value in cell.possible_values]
            assert len(cells) >= 1
            if len(cells) == 1:
                cells[0].set_value_to(value)
                print(f'Hidden Single: Ring = {value} must be {cells[0]}')
                result = True
        return result


    def check_even_more(self, sudoku: Sudoku) -> bool:
        sudoku.draw_grid()
        temp = sudoku.grid.matrix[2, 6]
        if len(temp.possible_values) == 2:
            print("Danger, danger")
            Cell.remove_value_from_cells([temp], 4)
            return True
        return False

    def draw(self, _sudoku: Sudoku) -> None:
        plt.gca().add_patch(plt.Circle((5.5, 5.5), radius=3, fill=False, facecolor='black'))

    def get_bridge(self, cell: Cell, adjacent: Cell, value: int):
        good_adjacent_values = self.MARVOLO_RING_INFO[value]
        bridge = adjacent.possible_values.intersection(good_adjacent_values)
        if cell.is_neighbor(adjacent) and value in bridge:
            bridge.discard(value)
        return bridge


class SnakeFeature(Feature):
    squares: Sequence[Tuple[int, int]]
    cells: Sequence[Cell]

    def __init__(self, squares: Sequence[Tuple[int, int]]):
        self.squares = squares

    def get_houses(self, grid: Grid) -> Sequence[House]:
        cells = [grid.matrix[square] for square in self.squares]
        return [House(House.Type.EXTRA, 0, cells)]

    def check(self, sudoku: Sudoku) -> bool:
        return False

    def draw(self, sudoku: Sudoku) -> None:
        self.draw_line(self.squares, color='lightgrey', linewidth=5)
        row, column = self.squares[0]
        plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor='lightgrey'))


class ContainsTextFeature(Feature):
    spans: List[List[Tuple[int, Cell]]]
    text: Sequence[int]
    row: int
    done: bool

    def __init__(self, row: int, text: Sequence[int]) -> None:
        super().__init__()
        self.row = row
        self.text = text

    def start_checking(self, sudoku: Sudoku) -> None:
        cells = [sudoku.grid.matrix[self.row, column] for column in range(1, 10)]
        self.spans = [list(zip(self.text, cells[i:])) for i in range(10 - len(self.text))]
        self.done = False

        for index, value in enumerate(self.text):
            legal_cells = [span[index][1]for span in self.spans]
            illegal_cells = [cell for cell in cells if cell not in legal_cells and value in cell.possible_values]
            Cell.remove_value_from_cells(illegal_cells, value)

    def check(self, sudoku: Sudoku) -> bool:
        if self.done:
            return False
        for span in self.spans:
            for value, cell in span:
                if cell.is_known and cell.known_value == value:
                    assert all(val in cel.possible_values for (val, cel) in span)
                    unknowns = [(val, cel) for (val, cel) in span if not cel.is_known]
                    if unknowns:
                        print(f"We can definitely place {self.text} starting at {span[0][1].index}")
                        for val, cel in unknowns:
                            cel.set_value_to(val, show=True)
                    self.done = True
                    return True
        for span in self.spans:
            for value, cell in span:
                if value not in cell.possible_values:
                    unknowns = [(val, cel) for (val, cel) in span if val in cel.possible_values]
                    if unknowns:
                        print(f"Text {self.text} definitely doesn't start at {span[0][1].index}")
                        for val, cel in unknowns:
                            Cell.remove_value_from_cells([cel], val)
                        return True
        return False


class ThermometerFeature(Feature):
    thermometer: Sequence[Tuple[int, int]]
    cells: Sequence[Cell]

    def __init__(self, thermometer: Sequence[Tuple[int, int]]):
        self.thermometer = thermometer

    def start_checking(self, sudoku: Sudoku) -> None:
        self.cells = [sudoku.grid.matrix[x] for x in self.thermometer]
        length = len(self.thermometer)
        span = 10 - length  # number of values each element in thermometer can have
        for minimum, cell in enumerate(self.cells, start=1):
            maximum = minimum + span - 1
            bad_values = list(range(1, minimum)) + list(range(maximum + 1, 10))
            Cell.remove_values_from_cells([cell], set(bad_values))

    def check(self, sudoku: Sudoku) -> bool:
        previous_cells = itertools.chain([None], self.cells)
        next_cells = itertools.chain(itertools.islice(self.cells, 1, None), itertools.repeat(None))
        for cell, previous_cell, next_cell in zip(self.cells, previous_cells, next_cells):
            impossible = set()
            for value in cell.possible_values:
                if previous_cell and value <= min(previous_cell.possible_values):
                    impossible.add(value)
                elif next_cell and value >= max(next_cell.possible_values):
                    impossible.add(value)
            if impossible:
                print("No appropriate value in adjacent cell")
                Cell.remove_values_from_cells([cell], impossible)
                return True
        return False

    def draw(self, sudoku: Sudoku) -> None:
        self.draw_line(self.thermometer, color='lightgrey', linewidth=5)
        row, column = self.thermometer[0]
        plt.gca().add_patch(plt.Circle((column + .5, row + .5), radius=.3, fill=True, facecolor='lightgrey'))


class EvenFeature(Feature):
    evens: Sequence[Tuple[int, int]]

    def __init__(self, evens: Sequence[Tuple[int, int]]):
        self.evens = evens

    def start_checking(self, sudoku: Sudoku) -> None:
        cells = [sudoku.grid.matrix[x] for x in self.evens]
        Cell.remove_values_from_cells(cells, {1, 3, 5, 7, 9})

    def check(self, sudoku: Sudoku) -> bool:
        pass


class CheckEggFeature(Feature):
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

    def start_checking(self, sudoku: Sudoku):
        for egg in self.eggs:
            size = len(egg.cells)
            Cell.remove_values_from_cells(egg.cells, set(range(len(egg.cells) + 1, 10)))

    def draw(self, sudoku: Sudoku) -> None:
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

    def start_checking(self, sudoku: Sudoku):
        for row, column in self.squares:
            value = self.__get_value(row, column)
            sudoku.grid.matrix[row, column].set_value_to(value)

    def __get_value(self, row: int, column: int) -> int:
        index = (row - 1) * 9 + (column - 1)
        value = sum(int(puzzle[index]) for puzzle in self.puzzles) % 9
        if value == 0:
            value = 9
        return value

    def draw(self, sudoku: Sudoku) -> None:
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

    def start_checking(self, sudoku: Sudoku):
        self.plus_feature.start_checking(sudoku)
        for (row, column), letter in self.setup.items():
            puzzle = self.color_map[letter]
            index = (row - 1) * 9 + (column - 1)
            value = int(puzzle[index])
            sudoku.grid.matrix[row, column].set_value_to(value)

    CIRCLES = dict(r="lightcoral", p="violet", o="bisque", g="lightgreen", G="lightgray", y="yellow", b="skyblue")

    def draw(self, sudoku: Sudoku) -> None:
        self.plus_feature.draw(sudoku)
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
                EvenFeature(evens),
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


def run_thermometer():
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

if __name__ == '__main__':
    puzzle8()
