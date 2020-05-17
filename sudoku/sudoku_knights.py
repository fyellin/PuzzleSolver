import itertools
from typing import Tuple, Sequence, Callable

from matplotlib import pyplot as plt

from solver import DancingLinks


class Sudoku:
    king: bool
    knight: bool

    def __init__(self, *, king: bool = False, knight: bool = False):
        self.king = king
        self.knight = knight

    def solve(self, puzzle: str):
        constraints = {}
        optional_constraints = set()
        initial_puzzle_grid = {(row, column): int(letter)
                               for (row, column), letter in zip(itertools.product(range(1, 10), repeat=2), puzzle)
                               if '1' <= letter <= '9'}
        for row, column in itertools.product(range(1, 10), repeat=2):
            values = [initial_puzzle_grid[row, column]] if (row, column) in initial_puzzle_grid else range(1, 10)
            for value in values:
                box = row - (row - 1) % 3 + (column - 1) // 3
                info = [f"Value{row}{column}", f"Row{row}={value}", f"Col{column}={value}", f"Box{box}={value}"]
                if self.knight:
                    for kr, kc in self.knights_move(row, column):
                        (min_row, min_column), (max_row, max_column) = sorted([(row, column), (kr, kc)])
                        info.append(f'N{min_row}:{min_column}||{max_row}:{max_column}={value}')
                if self.king:
                    for kr, kc in self.kings_move(row, column):
                        (min_row, min_column), (max_row, max_column) = sorted([(row, column), (kr, kc)])
                        info.append(f'K{min_row}:{min_column}||{max_row}:{max_column}={value}')


                optional_constraints.update(info[4:])
                constraints[(row, column, value)] = info
        links = DancingLinks(constraints, optional_constraints=optional_constraints,
                             row_printer=self.get_grid_printer(initial_puzzle_grid))
        links.solve(debug=1000, recursive=False)


    @staticmethod
    def knights_move(row: int, column: int) -> Sequence[Tuple[int, int]]:
        return [((row + dr), (column + dc))
                for dx, dy in itertools.product((1, -1), (2, -2))
                for dr, dc in ((dx, dy), (dy, dx))
                if 1 <= row + dr <= 9 and 1 <= column + dc <= 9]

    @staticmethod
    def kings_move(row: int, column: int) -> Sequence[Tuple[int, int]]:
        return [((row + dr), (column + dc))
                for dr, dc in itertools.product((-1, 1), repeat=2)
                if 1 <= row + dr <= 9 and 1 <= column + dc <= 9]

    @staticmethod
    def get_grid_printer(initial_puzzle_grid) -> Callable[[Sequence[Tuple[int, int, int]]], None]:
        def draw_grid(results: Sequence[Tuple[int, int, int]]) -> None:
            figure, axes = plt.subplots(1, 1, figsize=(4, 4), dpi=100)

            # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
            axes.axis([1, 10, 10, 1])
            axes.axis('equal')
            axes.axis('off')
            figure.tight_layout()

            # Draw the bold outline
            for x in range(1, 11):
                width = 3 if x in (1, 4, 7, 10) else 1
                axes.plot([x, x], [1, 10], linewidth=width, color='black')
                axes.plot([1, 10], [x, x], linewidth=width, color='black')

            given = dict(fontsize=13, color='black', weight='heavy')
            found = dict(fontsize=12, color='blue', weight='normal')
            for row, column, value in results:
                args = given if (row, column) in initial_puzzle_grid else found
                axes.text(column + .5, row + .5, str(value),
                          verticalalignment='center', horizontalalignment='center', **args)
            plt.show()

        return draw_grid


def main() -> None:
    puzzles = [
        "4........"
        "........." 
        "..8...7.."
        ".1......."
        "........."
        ".6...2.3."
        "..2...9.."
        "...7.4.1."
        "7.......5"
    ]
    Sudoku(knight=True).solve(puzzles[0])


if __name__ == '__main__':
    main()
