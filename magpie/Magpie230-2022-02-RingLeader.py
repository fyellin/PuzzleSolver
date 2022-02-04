import itertools
import re
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


def runner():
    # There are 3751 rows; 312 required constraints; 124 optional constraints
    # Count = 40509
    #  Solutions = 29628
    constraints = {}
    optional_constraints = set()

    def x(val):
        assert val in '01'
        return '1' if val == '0' else '0'

    for row, (holes, counts, rings) in enumerate(ROWS):
        for (string, ties) in get_line_info(holes, counts, rings, len(COLUMNS)):
            tie_constraints = {f'TIE-{row}-{column+delta}' for column in ties for delta in (0, 1)}
            optional_constraints |= tie_constraints
            constraints[('Row', row, string, *ties)] = [
                f'Row-{row}',
                *[f'{row}-{column}={value}' for column, value in enumerate(string)],
                *tie_constraints]

    for column, (holes, counts, rings) in enumerate(COLUMNS):
        for (string, ties) in get_line_info(holes, counts, rings, len(ROWS)):
            tie_constraints = {f'TIE-{row + delta}-{column}' for row in ties for delta in (0, 1)}
            optional_constraints |= tie_constraints
            constraints[('Column', column, string, *ties)] = [
                f'Column-{column}',
                *[f'{row}-{column}={x(value)}' for row, value in enumerate(string)],
                *tie_constraints]

    # noinspection PyTypeChecker
    solver = DancingLinks(constraints, optional_constraints=optional_constraints, row_printer=verify_and_show_grid)
    solver.solve(debug=0)


def verify_and_show_grid(constraints: Sequence[tuple[str, int, str, int, ...]]) -> None:
    def parse_grid_info(constraints) -> tuple[set[tuple[int, int]], list[Sequence[tuple[int, int], ...]]]:
        filled_cells = set()
        joins: list[Sequence[tuple[int, int], ...]] = []
        r_or_c: int
        for (my_type, r_or_c, string, *ties) in constraints:
            is_row = my_type == 'Row'
            if is_row:
                for column, value in enumerate(string):
                    if value == '1':
                        filled_cells.add((r_or_c, column))
            for start, end in parse_ties(ties):
                if is_row:
                    joins.append([(r_or_c, column) for column in range(start, end + 1)])
                else:
                    joins.append([(row, r_or_c) for row in range(start, end + 1)])
        assert len(filled_cells) == 54
        return filled_cells, joins

    def is_connected(cells):
        todo = cells.copy()
        queue = deque([todo.pop()])
        while queue:
            (row, col) = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + dr, col + dc)
                if neighbor in todo:
                    todo.remove(neighbor)
                    queue.append(neighbor)
        return len(todo) == 0

    filled_cells, joins = parse_grid_info(constraints)
    counter = Counter(len(x) for x in joins)

    if counter[2] == 14 and counter[4] == 3 and is_connected(filled_cells):
        show_grid(filled_cells, joins)


def show_grid(filled_cells: set[tuple[int, int]], joins: list[Sequence[tuple[int, int], ...]]) -> None:
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

    bbox_args = dict(boxstyle=(BoxStyle.Round(pad=.4, rounding_size=.4)), fill=False, linewidth=2)
    for join in joins:
        (start_row, start_col), *_, (end_row, end_col) = join
        filled_cells -= set(join)
        # noinspection PyTypeChecker
        patch = FancyBboxPatch((start_col + .5, start_row + .5), end_col - start_col, end_row - start_row, **bbox_args)
        axes.add_patch(patch)
    for (row, column) in filled_cells:
        # noinspection PyTypeChecker
        patch = FancyBboxPatch((column + .5, row + .5), 0, 0, **bbox_args)
        axes.add_patch(patch)
    plt.show()


@cache
def get_line_info(holes: int, count: int, rings: int, length: int) -> Sequence[tuple[str, tuple[int, ...]]]:
    result = []
    length_map = get_strings_for_length(length)
    for string in length_map[holes, count]:
        able_to_tie = [i for i, (c1, c2) in enumerate(pairwise(string)) if c1 == c2 == '1']
        for ties in combinations(able_to_tie, count - rings):
            if all(end - start in (1, 3) for start, end in parse_ties(list(ties))):
                result.append((string, ties))
    return result


@cache
def get_strings_for_length(length: int) -> Mapping[tuple[int, int], Sequence[str]]:
    result = defaultdict(list)
    for digits in itertools.product('01', repeat=length):
        string = ''.join(digits)
        count = string.count('1')
        holes = len(re.findall('0+', string))
        result[holes, count].append(string)
    return result


def parse_ties(items: list[int]) -> Iterable[tuple[int, int]]:
    while items:
        start = current = items.pop(0)
        while items and items[0] == current + 1:
            current = items.pop(0)
        yield start, current + 1


if __name__ == '__main__':
    runner()
