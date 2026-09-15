import itertools
from collections import defaultdict
from typing import Unpack

from matplotlib import pyplot as plt

from solver import DrawGridKwargs, EquationSolver

TEXT = """
The Earth is the only world known so far to harbor life.
There is nowhere else, at least in the near future, to which our species could migrate.
Visit, yes. Settle, not yet. Like it or not, for the moment the Earth is where we make our stand.
A mote of dust suspended in a sunbeam
"""

NUMBERS = {1: (2, 3),
           2: (2, 6),
           3: (3, 4),
           4: (3, 5),
           5: (3, 6),
           6: (4, 2),
           7: (4, 3),
           8: (4, 4),
           9: (4, 5),
           10: (4, 7),
           11: (5, 1),
           12: (6, 4),
           13: (7, 7),
           14: (8, 4),
           15: (8, 5),
           16: (9, 6),
           17: (10, 1),
           18: (10, 2),
           19: (10, 3),
           20: (11, 1),
           21: (11, 3),
           22: (11, 4),
           23: (12, 4),
           24: (12, 5),
           25: (12, 6),
           26: (14, 2),
           27: (14, 5),
           28: (16, 2),
           29: (16, 5),
           30: (16, 7),
           31: (17, 2),
           32: (18, 2),
           33: (18, 5),
           34: (20, 1),
           35: (20, 3),
           36: (20, 7),
           37: (21, 7),
           38: (22, 7),
           39: (23, 6),
           40: (24, 2),
           41: (24, 6),
           42: (25, 3),
           43: (25, 4)}

ASTERISKS = [(2, 4), (2, 7), (3, 1), (5, 2), (5, 6), (13, 3), (13, 4), (15, 5), (18, 1), (21, 2), (22, 6), (25, 3)]


class Foobar (EquationSolver):
    @staticmethod
    def run():
        solver = Foobar()
        solver.draw_grid()

    def draw_grid(self, **args: Unpack[DrawGridKwargs]) -> None:
        args["max_row"] = 26
        args["max_column"] = 8
        args["location_to_entry"] = {loc: string.upper() for loc, string in self.grid.items()}
        _, axes = plt.subplots(1, 1, figsize=(8, 25), dpi=300)
        args["axes"] = axes
        shading = args["shading"] = {}
        for square in self.grid:
            if len(self.origins[square]) > 2:
                shading[square] = 'red'
            if len(self.origins[square]) == 0:
                shading[square] = 'lightblue'
        clue_numbers = args["location_to_clue_numbers"] = {}
        for number, square in NUMBERS.items():
            clue_numbers[square] = [number]
        for square in ASTERISKS:
            if square not in clue_numbers:
                clue_numbers[square] = ["", '*']
            else:
                clue_numbers[square].append('*')
        super().draw_grid(**args)
        asterisks = [self.grid.get(square, '?') for square in ASTERISKS]
        print(''.join(asterisks))
        # plt.show()

    def __init__(self):
        self.grid = {}
        self.origins = defaultdict(set)
        for i in range(1, 8):
            self.grid[0, i] = str(i)
        for i in range(1, 26):
            self.grid[i, 0] = str(i)
        self.offset = 1
        self.draw_clue("42a", "duett")
        self.draw_clue("13d", "palaces")
        self.draw_clue("18d", "parasol")
        self.draw_clue("25d", "porrecting")

        self.offset = 2
        self.draw_clue("35d", "actusrei")
        self.draw_clue("20a", "spec")
        self.draw_clue("2d", "three")

        self.offset = 3
        self.draw_clue("33a", "aten")
        self.draw_clue("15d", "dealwith")
        self.draw_clue("26d", "spinal")

        self.offset = 4
        self.draw_clue("22d", "moerae")
        self.draw_clue("43a", "unwaters")

        self.offset = 5
        self.draw_clue("38d", "cetus")
        self.draw_clue("8a", "screeve")
        self.draw_clue("23d", "visa")

        self.offset = 6
        self.draw_clue("34a", "begirt")
        self.draw_clue("14d", "enswathe")
        self.draw_clue("17d", "ipad")
        self.draw_clue("24d", "oar")

        self.offset = 7
        self.draw_clue("30d", "amputator")
        self.draw_clue("6d", "fauve")
        self.draw_clue("3d", "shia")

        self.offset = 8
        self.draw_clue("27a", "arak")
        self.draw_clue("5a", "sluicier")
        self.draw_clue("32a", "unset")

        self.offset = 9
        self.draw_clue("4d", "doe")
        self.draw_clue("36d", "eleanor")
        self.draw_clue("37a", "enate")
        self.draw_clue("31a", "principal")

        self.offset = 10
        self.draw_clue("39d", "jaeger")
        self.draw_clue("10a", "leal")
        self.draw_clue("21d", "pein")

        self.offset = 11
        self.draw_clue("16d", "anlage")

        self.offset = 12
        self.draw_clue("41a", "dud")
        self.draw_clue("6a", "frau")
        self.draw_clue("39d", "jacent")

        self.offset = 13
        self.draw_clue("29a", "ararat")
        self.draw_clue("19a", "trenchfever")

        self.offset = 14
        self.draw_clue("7d", "liefer")
        self.draw_clue("28d", "lines")

        self.offset = 15
        self.draw_clue("12a", "idee")
        self.draw_clue("11a", "pium")
        self.draw_clue("25a", "pusher")
        self.draw_clue("40a", "rascal")

        self.offset = 16
        self.draw_clue("9d", "owrie")
        self.draw_clue("1a", "rollmop")

        self.find_planet("mercury", 1)
        self.find_planet("venus", 3)
        self.find_planet("earth", 4)
        self.find_planet("jupiter", 49)
        self.find_planet("saturn", 122)
        self.find_planet("uranus", 349)
        self.find_planet("neptune", 684)
        self.find_planet("pluto", 1030)
        self.find_planet("mars", 8)

        self.find_word("sunbeam")
        self.find_word("youare")
        self.find_word("hoaor")

    def get_clue_squares(self, square: tuple[int, int], is_across: bool, offset: int, length: int) -> list[tuple[int, int]]:
        row, column = square
        result = [square]
        while len(result) < length:
            if is_across:
                column += offset
                while column >= 8:
                    row, column = row + 1, column - 7
                while row >= 26:
                    row -= 25
            else:
                row += offset
                while row >= 26:
                    row, column = row - 25, column + 1
                while column >= 8:
                    column -= 7
            result.append((row, column))
        return result

    def draw_clue(self, name: str, word: str):
        squares = self.get_clue_squares_from_name(name, self.offset, len(word))
        for index, (letter, square) in enumerate(zip(word, squares, strict=True), start=1):
            if self.grid.get(square, letter) == letter:
                self.grid[square] = letter
                self.origins[square].add((name, word, index))
            else:
                print(f"Failure at (square): {word}:{index}: {self.origins[square]}")

    def get_info(self, name: str, offset: int, length: int):
        squares = self.get_clue_squares_from_name(name, offset, length)
        result = [self.grid.get(square, '?') for square in squares]
        print(name, ''.join(result))

    def get_clue_squares_from_name(self, name: str, offset: int,
                                   length: int) -> list[tuple[int, int]]:
        start_square = NUMBERS[int(name[:-1])]
        is_across = name[-1] == "a"
        return self.get_clue_squares(start_square, is_across, offset, length)

    def find_planet(self, name: str, offset: int, insert: bool = True):
        results = []
        for start_square in itertools.product(range(1, 26), range(1, 8)):
            squares = self.get_clue_squares(start_square, True, offset, len(name))
            letters = [self.grid.get(square, '?') for square in squares]
            if all(x == y or y == '?' for x, y in zip(name, letters, strict=True)):
                results.append(squares)
        if len(results) == 1 and insert:
            squares = results[0]
            for square, letter in zip(squares, name, strict=True):
                assert self.grid.get(square, letter) == letter
                self.grid[square] = letter
        return results

    def find_word(self, word: str, insert: bool = True):
        results = []
        for start_square in itertools.product(range(1, 26), range(1, 8)):
            for offset in range(1, 175):
                for direction in (True,):
                    squares = self.get_clue_squares(start_square, direction, offset, len(word))
                    letters = [self.grid.get(square, '?') for square in squares]
                    if all(x == y or y == '?' for x, y in zip(word, letters, strict=True)):
                        results.append(squares)
        if len(results) == 1 and insert:
            squares = results[0]
            for square, letter in zip(squares, word, strict=True):
                assert self.grid.get(square, letter) == letter
                self.grid[square] = letter
        return results


class Foobar2 (EquationSolver):
    @staticmethod
    def run():
        solver = Foobar2()
        solver.draw_grid()

    def __init__(self):
        # self.image = mpimg.imread("/users/fy/Desktop/Pale Blue Dot.png")
        pass

    def draw_grid(self, **args: Unpack[DrawGridKwargs]) -> None:
        max_column, max_row = 8, 26

        def extra(plt, axes):
            self.draw_line([(1.5, 7.5), (25.5, 1.5)], lw=30, color="yellow")
            self.draw_line([(12.5, 3.5), (17.4, 3.5), (15.5, 1.5),
                            (17.6, 3.5), (15.5, 5.5), (17.4, 3.5)], lw=3, color="red")
            axes.scatter([3.5], [17.5], s=400, color="xkcd:pale blue", zorder=3)
            for row in range(1, max_row + 1):
                self.draw_line([(row, 1), (row, max_column)], color="white")
            for column in range(1, max_column + 1):
                self.draw_line([(1, column), (max_row, column)], color="white")

        _, axes = plt.subplots(1, 1, figsize=(8, 25), dpi=300)
        args["axes"] = axes
        args["max_row"] = max_row
        args["max_column"] = max_column
        args["location_to_entry"] = {}
        args["extra"] = extra
        shading = dict.fromkeys(itertools.product(range(1, 26), range(1, 8)), "black")
        args["shading"] = shading
        args["subtext"] = "YOU ARE HERE"
        args["grid_drawer"] = lambda *args: None
        super().draw_grid(**args)
        plt.show()

    def draw_line(self, points, **args):
        y, x = zip(*points, strict=True)
        plt.plot(x, y, **args)


if __name__ == '__main__':
    Foobar2.run()
