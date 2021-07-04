from typing import Sequence, Set

from cell import Cell, House
from feature import Feature, Square
from grid import Grid

from itertools import combinations
from draw_context import DrawContext


class QuadrupleFeature(Feature):
    grid: Grid
    squares: Sequence[Square]
    values: Set[int]
    cells: Sequence[Cell]

    current_cells = Set[Cell]
    current_values = Set[int]
    done: bool

    def __init__(self, square: Square, values: Sequence[int]):
        row, column = square
        self.squares = [(row, column), (row, column + 1), (row + 1, column + 1), (row + 1, column)]
        self.values = set(values)

    def initialize(self, grid: Grid) -> None:
        self.grid = grid
        self.cells = [grid.matrix[square] for square in self.squares]
        if len(self.values) == 4:
            Cell.keep_values_for_cell(self.cells, self.values, show=False)

        self.current_cells = set(self.cells)
        self.current_values = set(self.values)
        self.done = False

    def __str__(self) -> str:
        row, column = self.squares[0]
        return f'<{"".join(str(value) for value in sorted(self.values))}@r{row}c{column}>'

    @Feature.check_only_if_changed
    def check(self) -> bool:
        if self.done:
            return False
        if not self.current_values:
            # All values have been assigned.  We never need to be looked at, again.
            self.done = True
            return False
        assert len(self.current_cells) >= len(self.current_values)

        changes = False

        deletions = set()
        for cell in self.current_cells:
            if cell.is_known:
                deletions.add(cell)
                self.current_values.discard(cell.known_value)
            elif not cell.possible_values.intersection(self.current_values):
                deletions.add(cell)
        self.current_cells.difference_update(deletions)

        # If all the cells are in the same box, we can just do the cheapo method, and be done with this.
        # Remove the digits from every other cell in the box, so they must eventually appear here
        if len(set(cell.house_of_type(House.Type.BOX) for cell in self.current_cells)) == 1:
            box = next(iter(self.current_cells)).house_of_type(House.Type.BOX)
            for cell in box.unknown_cells:
                if cell not in self.current_cells and cell.possible_values.intersection(self.values):
                    if not changes:
                        print(f'Quadruple {self} now all in {box}. Remove values from elsewhere in box.')
                    changes = True
                    Cell.remove_values_from_cells([cell], self.current_values, show=True)
            self.done = True

        if len(self.current_cells) == len(self.current_values):
            for cell in self.current_cells:
                if not cell.possible_values.issubset(self.current_values):
                    if not changes:
                        print(f'Quadruple {self} has {len(self.current_cells)} cells and values')
                    Cell.keep_values_for_cell([cell], self.current_values, show=True)
                    changes = True

        if changes:
            return True

        for count in range(1, len(self.current_values)):
            for values in combinations(self.current_values, count):
                values = set(values)
                possible_locations = [cell for cell in self.current_cells if cell.possible_values.intersection(values)]
                assert len(possible_locations) >= count
                if len(possible_locations) == count:
                    for cell in possible_locations:
                        if cell.possible_values.difference(values):
                            if not changes:
                                print(f'Only {count} possible locations for values {values} in {self}')
                            cell.keep_values_for_cell([cell], values)
                            changes = True
                if changes:
                    return True

        return False

    def draw(self, context: DrawContext) -> None:
        y, x = self.squares[0]
        context.draw_circle((x + 1, y + 1), radius=.2, fill=False)
        text = ' '.join(str(x) for x in self.values)
        if len(self.values) >= 3:
            text = text[0:3] + '\n' + text[4:]
        context.draw_text(x + 1, y + 1, text,
                          fontsize=10,
                          verticalalignment='center', horizontalalignment='center', color='black')
