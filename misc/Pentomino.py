import itertools
from functools import cache

import matplotlib.pyplot as plt
from matplotlib import patches


class Pentomino:
    PENTOMINOS = {
        'F': [(1, 2), (1, 3), (2, 1), (2, 2), (3, 2)],
        'I': [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1)],
        'L': [(1, 1), (2, 1), (3, 1), (4, 1), (4, 2)],
        'N': [(1, 2), (2, 2), (3, 1), (3, 2), (4, 1)],
        'P': [(1, 1), (1, 2), (2, 1), (2, 2), (3, 1)],
        'T': [(1, 1), (1, 2), (1, 3), (2, 2), (3, 2)],
        'U': [(1, 1), (1, 3), (2, 1), (2, 2), (2, 3)],
        'V': [(1, 1), (2, 1), (3, 1), (3, 2), (3, 3)],
        'W': [(1, 1), (2, 1), (2, 2), (3, 2), (3, 3)],
        'X': [(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)],
        'Y': [(1, 3), (2, 1), (2, 2), (2, 3), (2, 4)],
        'Z': [(1, 1), (1, 2), (2, 2), (3, 2), (3, 3)]
    }

    @classmethod
    def get_all_pentominos(cls, rows, columns=None):
        columns = rows or columns
        size = max(columns, rows)
        results = {}
        for name, cells in cls.PENTOMINOS.items():
            items = {frozenset(cells)}
            items = {frozenset((r + dr, c + dc) for (r, c) in pentomino)
                     for pentomino in items
                     for dr, dc in itertools.product(range(size), repeat=2)
                     if dr + max(rr for rr, _ in pentomino) <= size
                     if dc + max(cc for _, cc in pentomino) <= size}
            items |= {frozenset((8 - r, c) for r, c in pentomino) for pentomino in items}
            items |= {frozenset((r, 8 - c) for r, c in pentomino) for pentomino in items}
            items |= {frozenset((c, 8 - r) for r, c in pentomino) for pentomino in items}
            if rows != columns:
                items = {pentomino for pentomino in items
                         if all(r <= rows and c <= columns for r, c in pentomino)}
            results[name] = items
        return results


class Tiling:
    map: dict[tuple[int, int], str]
    name: str
    size: int

    def __init__(self, arg, size):
        squares = ((r, c) for r in range(1, size + 1) for c in range(1, size + 1))
        if isinstance(arg, str):
            self.name = arg
            self.map = dict(zip(squares, self.name))
        else:
            self.map = arg
            self.name = ''.join(arg[square] for square in squares)
        self.size = size
        assert len(self.name) == len(self.map) == size * size

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.name}", {self.size})'

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def show(self, *, axis=None, mapping=None, white: bool = False):
        if mapping is None:
            mapping = dict()
        if axis is None:
            _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)
        else:
            axes = axis
        max_row = max_column = self.size + 1

        # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
        axes.axis([1, max_column, max_row, 1])
        axes.axis('equal')
        axes.axis('off')

        color_map = self.get_color_map()
        for (row, column), name in self.map.items():
            color = color_map[name]
            if not white or name == '-':
                axes.add_patch(
                    patches.Rectangle((column, row), 1, 1, facecolor=color, linewidth=0))
            if name in mapping:
                axes.text(column + .5, row + .5, str(mapping[name]),
                          fontsize=20, fontweight='bold',
                          fontfamily="sans-serif",
                          verticalalignment='center', horizontalalignment='center')

        for row in range(1, max_row):
            for column in range(1, max_column + 1):
                width = 1 + 3 * ((row, column) in [
                    (1, 5), (3, 4), (4, 3), (4, 6), (5, 5), (7, 4)])
                plt.plot((column, column), (row, row + 1), color='black', linewidth=width)

        for row in range(1, max_row + 1):
            for column in range(1, max_column):
                width = 1 + 3 * ((row, column) in [
                    (3, 4), (4, 1), (4, 5), (5, 3), (5, 7), (6, 4)])
                plt.plot((column, column + 1), (row, row), color='black', linewidth=width)

        plt.plot((1, 1), (2, 2))
        if axis is None:
            plt.show()

    @staticmethod
    @cache
    def get_color_map():
        colors = ["black", "#C80000", "#9696FF", "#00C8C8", "#FF96FF", "#00C800",
                  "#96FFFF", "#969600", "#C900C0", "#FF9696", "#0000C8", "#FFFF96",
                  "#96FF96"]
        tiles = "-FILNPTUVWXYZ"
        return dict(zip(tiles, colors))


def intersection_printer(list_of_tiles, size):
    _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)
    max_row = max_column = 8

    # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
    axes.axis([1, max_column, max_row, 1])
    axes.axis('equal')
    axes.axis('off')

    for row, column in itertools.product(range(1, size + 1), repeat=2):
        axes.add_patch(patches.Rectangle((column, row), 1, 1,
                                         facecolor='black', fill=False, linewidth=1))

    for i, tiles in enumerate(list_of_tiles, start=0):
        for row, column in tiles:
            axes.text(column + 1 / 2, row + 1 / 2, str(chr(97 + i)),
                      fontsize=20, fontweight='bold',
                      fontfamily="sans-serif",
                      verticalalignment='center', horizontalalignment='center')
        for (r1, c1), (r2, c2) in itertools.combinations(sorted(tiles), 2):
            if r1 == r2 and c2 == c1 + 1:
                plt.plot((c1 + .5, c2 + .5), (r1 + .5, r2 + .5),
                         linewidth=1, color='black')
            elif c2 == c1 and r2 == r1 + 1:
                plt.plot((c1 + .5, c2 + .5), (r1 + .5, r2 + .5),
                         linewidth=1, color='black')

    plt.show()
