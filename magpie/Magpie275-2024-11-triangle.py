import itertools
from collections.abc import Sequence

from matplotlib import pyplot as plt

from solver import DancingLinks

Square = tuple[int, int]

def next_triangle(square: Square, direction: int) -> Square:
    (row, column) = square
    is_regular = column % 2 == 1
    match (is_regular, direction % 3):
        case (True, 0):
            result = row + 1, column + 1
        case (False, 0):
            result = row - 1, column - 1
        case (True, 2) | (False, 1):
            result = row, column + 1
        case (False, 2) | (True, 1):
            result = row, column - 1
    return result

def parse_recipe(start: Square, recipe: str, direction: int) -> tuple[Square, ...]:
    result = [start, last := next_triangle(start, direction)]
    saved = None
    for ch in recipe:
        if ch == 'l':
            direction += 1
            result.append(last := next_triangle(last, direction))
        elif ch == 'r':
            direction -= 1
            result.append(last := next_triangle(last, direction))
        elif ch == '*':
            saved = last, direction
        elif ch == '/':
            last, direction = saved
    assert len(set(result)) == 6
    return tuple(result)


RECIPES = [
    "rlrl", "llrl", "l*rl/l",
    "*lrl/r", "rllr", "*rll/l",
    "l*lr/r", "*lr/rl", "lrrr",
    "llrr", "rrrr", "*l/r*l/r"
]

VALUES = "504230245523 154011310541 235523345430 043021020221 245324513115 053141044230".split()

def draw_triangle(squares: Sequence[Square], area) -> None:
    figure, axis = plt.subplots(1, 1, dpi=300)
    axis.set_aspect('1.7')
    axis.axis('off')
    for index, square in enumerate(squares, start = 1):
        shape = HEX_MAP[square]
        color = 'lightgreen' if shape in area[0] else 'lightblue' if shape in area[1] else 'yellow'
        color = 'white'
        row, col = square
        x, y = col - row, -row
        text = VALUES[row - 1][col - 1]
        if col % 2 == 0:
            point, a, b, toff = (x, y), (x - 1, y + 1), (x + 1, y + 1), .6
        else:
            point, a, b, toff = (x, y + 1), (x + 1, y), (x - 1, y), .3
        xs, ys = zip(point, a, b, point)
        axis.fill(xs, ys, lw=0.5, color='black', fc=color)
        axis.text(x, y + toff, text, fontsize=15, fontweight='bold',
                  va='center', ha='center')

        # near_shapes = [HEX_MAP.get(next_triangle(square, direction)) for direction in (0, 1, 2)]
        # if near_shapes[0] != shape:
        #     axis.plot(*zip(a, b), lw=2, color='black')
        # if near_shapes[1] != shape:
        #     axis.plot(*zip(point, b), lw=2, color='black')
        # if near_shapes[2] != shape:
        #     axis.plot(*zip(point, a), lw=2, color='black')
    plt.show()

def draw_map(area):
    triangles = list(itertools.product(range(1, 7), range(1, 13)))
    draw_triangle(triangles, area)


def dancing_links(debug=False):
    constraints = {}
    for (index, recipe) in enumerate(RECIPES, start = 1):
        results = set()
        for original in (True, False):
            if not original:
                recipe = recipe.replace("l", "x").replace("r", "l").replace("x", "r")
            for direction in (0, 1, 2):
                for start in itertools.product(range(1, 7), range(1, 13)):
                    result = frozenset(parse_recipe(start, recipe, direction))
                    if all(1 <= r <= 6 and 1 <= c <= 12 for (r, c) in result):
                        results.add(result)
        for result in results:
            values = {VALUES[row - 1][col - 1] for row, col in result}
            if len(values) == 6:
                name = (index, tuple(sorted(result)))
                values = [f'SHAPE-{index}']
                values.extend(f'r{row}c{col}' for row, col in sorted(result))
                constraints[name] = values

    result = None
    def my_row_printer(info):
        nonlocal result
        assert result is None
        result = {index : cells for (index, cells) in info}

    solver = DancingLinks(constraints, row_printer=my_row_printer)
    solver.solve(debug=debug)
    return result


RESULTS = {
    1: ((2, 1), (2, 2), (3, 1), (3, 2), (4, 1), (4, 2)),
    2: ((1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (2, 6)),
    3: ((4, 7), (4, 8), (5, 7), (5, 8), (5, 9), (6, 8)),
    4: ((1, 10), (1, 11), (1, 12), (2, 11), (2, 12), (3, 12)),
    5: ((5, 11), (5, 12), (6, 9), (6, 10), (6, 11), (6, 12)),
    6: ((5, 3), (5, 4), (5, 5), (6, 5), (6, 6), (6, 7)),
    7: ((1, 6), (1, 7), (1, 8), (1, 9), (2, 7), (2, 8)),
    8: ((5, 1), (5, 2), (6, 1), (6, 2), (6, 3), (6, 4)),
    9: ((3, 7), (3, 8), (3, 9), (4, 9), (4, 10), (5, 10)),
    10: ((2, 9), (2, 10), (3, 10), (3, 11), (4, 11), (4, 12)),
    11: ((2, 3), (2, 4), (2, 5), (3, 4), (3, 5), (3, 6)),
    12: ((3, 3), (4, 3), (4, 4), (4, 5), (4, 6), (5, 6)),
}

HEX_MAP = {square: hex for hex, squares in RESULTS.items() for square in squares}

def get_neighbors():
    all_neighbors = set()
    neighbors = { index: {square for cell in RESULTS[index]
                          for direction in (0, 1, 2)
                          for square in [next_triangle(cell, direction)]
                          if HEX_MAP.get(square, index) != index}
                  for index in range(1, 13)
                  }
    for index1, index2 in itertools.combinations(range(1, 13), 2):
        result1 = neighbors[index1].isdisjoint(set(RESULTS[index2]))
        result2 = neighbors[index2].isdisjoint(set(RESULTS[index1]))
        assert result1 == result2
        if not result1:
            all_neighbors.add((index1, index2))
            all_neighbors.add((index2, index1))

    color_maps1 = set()
    color_maps2 = set()
    decoder = {}
    for a, b, c, d in itertools.combinations(range(1, 13), 4):
        if any((x, y) in all_neighbors for x, y in itertools.combinations((a, b, c, d), 2)):
            continue
        code = (1 << a) + (1 << b) + (1 << c) + (1 << d)
        decoder[code] = (a, b, c, d)
        if a == 1:
            color_maps1.add(code)
        else:
            color_maps2.add(code)

    print(len(color_maps1), len(color_maps2))

    for value1, value2 in itertools.product(color_maps1, color_maps2):
        if value1 & value2 == 0:
            value3 = 0x1FFE - value1 - value2
            if value3 in color_maps2:
                print(decoder[value1], decoder[value2], decoder[value3])

AREA = [(1, 5, 6, 7), (3, 8, 10, 11), (2, 4, 9, 12)]


if __name__ == '__main__':
    draw_map(AREA)
    # dancing_links(debug=True)

