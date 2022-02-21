import itertools
from collections import Counter, defaultdict, deque
from collections.abc import Mapping, Sequence, Iterable
from functools import cache
from itertools import combinations, pairwise

import matplotlib.pyplot as plt
from matplotlib.patches import BoxStyle, FancyBboxPatch

from solver import DancingLinks

ROWS = [(2, 1, 1), (3, 3, 2), (3, 3, 2), (2, 7, 4), (2, 7, 4), (3, 5, 2), (3, 6, 3), (2, 4, 2), (2, 4, 2),
        (3, 2, 2), (3, 4, 2), (3, 4, 2), (3, 4, 2)]
COLUMNS = [(1, 0, 0), (1, 0, 0), (1, 5, 5), (2, 5, 4), (2, 9, 9), (2, 8, 8), (2, 8, 8),
           (2, 9, 9), (2, 5, 4), (2, 4, 4), (2, 1, 1), (1, 0, 0)]


Constraint = tuple[str, int, tuple[int], tuple[tuple[int, int]]]


def runner():
    constraints: dict[Constraint, list[str]] = {}
    optional_constraints: set[str] = set()

    for row, (holes, counts, rings) in enumerate(ROWS):
        for (digits, ties) in get_line_info(holes, counts, rings, len(COLUMNS)):
            tie_constraints = {f'TIE-{row}-{column}'
                               for start, end in ties
                               for column in range(start, end + 1)}
            optional_constraints |= tie_constraints
            constraints[('Row', row, digits, ties)] = [
                f'Row-{row}',
                *[f'{row}-{column}={int(column in digits)}' for column in range(len(COLUMNS))],
                *tie_constraints]

    for column, (holes, counts, rings) in enumerate(COLUMNS):
        for (digits, ties) in get_line_info(holes, counts, rings, len(ROWS)):
            tie_constraints = {f'TIE-{row}-{column}'
                               for start, end in ties
                               for row in range(start, end + 1)}
            optional_constraints |= tie_constraints
            constraints[('Column', column, digits, ties)] = [
                f'Column-{column}',
                *[f'{row}-{column}={int(row not in digits)}' for row in range(len(ROWS))],
                *tie_constraints]

    solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                          row_printer=Printer().run_printer)
    solver.solve(debug=0)


class Printer:
    filled_cells: set[tuple[int, int]]
    joins: list[Sequence[tuple[int, int], ...]]

    def run_printer(self, constraints: Sequence[Constraint]) -> None:
        self.__parse_constraints(constraints)
        if self.__verify_result():
            self.__show_result()

    def __parse_constraints(self, constraints: Sequence[Constraint]) -> None:
        self.filled_cells = set()
        self.joins = []
        for (my_type, r_or_c, digits, ties) in constraints:
            is_row = my_type == 'Row'
            if is_row:
                self.filled_cells.update((r_or_c, column) for column in digits)
            for start, end in ties:
                if is_row:
                    self.joins.append([(r_or_c, column) for column in range(start, end + 1)])
                else:
                    self.joins.append([(row, r_or_c) for row in range(start, end + 1)])
        assert len(self.filled_cells) == 54

    def __verify_result(self) -> bool:
        counter = Counter(len(x) for x in self.joins)
        if counter[2] != 14 or counter[4] != 4:
            return False

        todo = self.filled_cells.copy()
        queue = deque([todo.pop()])
        while queue:
            (row, col) = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + dr, col + dc)
                if neighbor in todo:
                    todo.remove(neighbor)
                    queue.append(neighbor)
        return len(todo) == 0

    def __show_result(self) -> None:
        _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)
        max_column = 12
        max_row = 13
        # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
        axes.axis([0, max_column + 1, max_row + 1, 0])
        axes.axis('equal')
        axes.axis('off')
        # draw grid
        for column in range(0, max_column + 1):
            axes.plot([column, column], [0, max_row], color='black')
        for row in range(0, max_row + 1):
            axes.plot([0, max_column], [row, row], 'black')
        # draw the numbers
        for row, (holes, count, rings) in enumerate(ROWS):
            axes.text(max_column + .1, row + .5, f'{holes} {count} {rings}',
                      verticalalignment='center', horizontalalignment='left', fontweight='bold', fontsize=20)
        for column, (holes, count, rings) in enumerate(COLUMNS):
            axes.text(column + .5, max_row + .1, f'{holes}\n{count}\n{rings}',
                      verticalalignment='top', horizontalalignment='center', fontweight='bold', fontsize=20)

        seen: set[tuple[int, int]] = set()
        bbox_args = dict(boxstyle=(BoxStyle.Round(pad=.4, rounding_size=.4)),
                         fill=True, linewidth=2, fc="gray")
        for join in self.joins:
            (start_row, start_col), *_, (end_row, end_col) = join
            seen.update(join)
            # noinspection PyTypeChecker
            patch = FancyBboxPatch((start_col + .5, start_row + .5),
                                   end_col - start_col, end_row - start_row, **bbox_args)
            axes.add_patch(patch)

        for (row, column) in self.filled_cells - seen:
            # noinspection PyTypeChecker
            patch = FancyBboxPatch((column + .5, row + .5), 0, 0, **bbox_args)
            axes.add_patch(patch)
        plt.show()


@cache
def get_line_info(holes: int, count: int, rings: int, length: int) -> \
        Sequence[tuple[tuple[int], Sequence[tuple[int, int]]]]:
    result = []
    for digits in get_strings_for_length_count(length, count)[holes]:
        joinable_to_next = [i for i, j in pairwise(digits) if i == j - 1]
        for joined_to_next in combinations(joinable_to_next, count - rings):
            ties = tuple(parse_ties(joined_to_next))
            if all(end + 1 - start in (1, 2, 4) for start, end in ties):
                result.append((digits, ties))
    return result


def parse_ties(items: tuple[int]) -> Iterable[tuple[int, int]]:
    items = list(items)
    while items:
        start = current = items.pop(0)
        while items and items[0] == current + 1:
            current = items.pop(0)
        yield start, current + 1


@cache
def get_strings_for_length_count(length: int, count: int) -> Mapping[int, Sequence[tuple[int]]]:
    result = defaultdict(list)
    for digits in itertools.combinations(range(length), count):
        chain = itertools.chain((-1,), digits, (length,))
        holes = sum(i != j - 1 for i, j in itertools.pairwise(chain))
        result[holes].append(digits)
    return result


if __name__ == '__main__':
    runner()
