from time import time
from itertools import combinations, groupby, product
from math import comb
from typing import Callable

from matplotlib import pyplot as plt


C_LINE = ('DE', 'EZ', 'DZ', 'DG', 'KZ', 'AG', 'EG', ('BE', 'BK'), 'BD', 'EK',
          ('BZ', 100), 'GZ', 'DK', 'AD', 'AE', 'AZ', 'BG', 'GK', 'AK', 'AB')

R_LINE = ('DE', 'EZ', 'KZ', 'DZ', 'DG', 'AG', 'BK', 'EG', 'AK', 'EK', 'AZ',
          'BG', 'DK', 'BD', 'BE', 'GZ', ('AE', 'BZ'), 'AD', 'GK', 'AB')


def parse_one_constraint(item: str|int|tuple[str,str], func:Callable[[int, int], int]):
    if isinstance(item, str):
        name1, name2 = item

        def result(points):
            point1, point2 = points.get(name1), points.get(name2)
            if point1 and point2:
                (x1, y1), (x2, y2) = point1, point2
                return func(abs(x2 - x1), abs(y2 - y1))
            return None
        return result
    if isinstance(item, int):
        return lambda points: 100
    if isinstance(item, tuple):
        result1, result2 = [parse_one_constraint(x, func) for x in item]

        def result(points):
            value1, value2 = result1(points), result2(points)
            if value1 and value2 and value1 != value2:
                return -1
            return value1 or value2
        return result
    assert False


C_LINE_COMPILED = [parse_one_constraint(x, lambda x, y: x * x + y * y) for x in C_LINE]
R_LINE_COMPILED = [parse_one_constraint(x, lambda x, y: comb(x + y, y)) for x in R_LINE]


def check_constraints(points):
    for line in (C_LINE_COMPILED, R_LINE_COMPILED):
        last_value = 0
        for item in line:
            value = item(points)
            if value:
                if value <= last_value:
                    return False
                last_value = value
    return True


def solve(draw=False):
    counts = [0] * 8
    order = "ABZDEGK"   # 1 151 29 23, 2, 1, 1
    order = "ABZEGKD"   # 1 151 29 5, 1, 1, 1

    def internal(points, index):
        counts[len(points)] += 1
        points = points.copy()
        try:
            variable = order[index]
        except IndexError:
            print(points)
            if draw:
                draw_grid(**points)
            return
        for point in product(range(1, 21), range(1, 13)):
            points[variable] = point
            if check_constraints(points):
                internal(points, index + 1)

    internal({'A': (1, 1)}, 1)
    print(counts[1:])


def draw_grid(annotate=1, **args):
    _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)
    max_column = 12
    max_row = 20

    # set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
    axes.axis([1, max_column, max_row, 1])
    axes.axis('equal')
    axes.axis('off')

    for row in range(1, max_row + 1):
        axes.plot([1, max_column], [row, row], color='black', lw=.5)
    for column in range(1, max_column + 1):
        axes.plot([column, column], [1, max_row], color='black', lw=.5)

    greek_map = dict(A="alpha", B="beta", D="delta", G="gamma",
                     E="epsilon", K="kappa", Z="zeta")
    for key, (row, column) in args.items():
        axes.add_patch(plt.Circle((column, row),
                                  radius=.3, linewidth=2, fill=True, fc='red'))
        if annotate == 1:
            dc, dr = .6, 0
            if key in 'AZ':
                dr += .3
            if key == 'B':
                dc = -dc
            if key == 'K':
                dr -= .3
            axes.text(column + dc, row + dr, f'$\\{greek_map[key]}$',
                      fontsize=20, fontweight='bold',
                      fontfamily="sans-serif", va='center', ha='center')

    for line in ('DE', 'EZ', 'DG', 'KZ', 'BD', 'AZ'):
        (r1, c1) = args[line[0]]
        (r2, c2) = args[line[1]]
        axes.plot([c1, c2], [r1, r2], color='blue', lw=3)

    axes.text((max_column + 1) / 2, max_row + .2, "ORION",
              fontsize=20, fontweight='bold',
              fontfamily="sans-serif", va='top', ha='center')

    plt.show()

def verifier():
    values = {'A': (1, 1), 'B': (18, 12), 'Z': (12, 4), 'E': (11, 6), 'G': (3, 9), 'K': (20, 3), 'D': (10, 7)}
    keys = sorted(values.keys())

    a = [('100', 100)]
    b = []
    for key1, key2 in combinations(keys, 2):
        (x1, y1), (x2, y2) = values[key1], values[key2]
        dx, dy = abs(x2 - x1), abs(y2 - y1)
        a.append((key1 + key2, dx ** 2 + dy ** 2))
        b.append((key1 + key2, comb(dx + dy, dx)))

    for values in (a, b):
        values.sort(key = lambda x: x[1])
        for value, items in groupby(values, lambda x: x[1]):
            print(value, [x for x, _ in items])


if __name__ == '__main__':
    # verifier()
    start = time()
    solve(draw=True)
    print(time() - start)
