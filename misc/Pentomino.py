import itertools
from collections import defaultdict
from collections.abc import Sequence
from functools import cache

from misc.UnionFind import UnionFind
from solver import DancingLinks
from solver.draw_grid import draw_grid


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
        columns = columns or rows
        size = max(columns, rows)
        results = {}
        for name, cells in cls.PENTOMINOS.items():
            items = {frozenset(cells)}
            items = {frozenset((r + dr, c + dc) for (r, c) in pentomino)
                     for pentomino in items
                     for max_r in [max(rr for rr, _ in pentomino)]
                     for max_c in [max(rr for rr, _ in pentomino)]
                     for dr in range(0, size + 1 - max_r)
                     for dc in range(0, size + 1 - max_c)}
            items |= {frozenset((size + 1 - r, c) for r, c in pentomino)
                      for pentomino in items}
            items |= {frozenset((size + 1, 8 - c) for r, c in pentomino)
                      for pentomino in items}
            items |= {frozenset((c, size + 1 - r) for r, c in pentomino)
                      for pentomino in items}
            if rows != columns:
                items = {pentomino for pentomino in items
                         if all(1 <= r <= rows and 1 <= c <= columns
                                for r, c in pentomino)}
            results[name] = items
        return results


class Tiling:
    map: dict[tuple[int, int], str]
    string: str
    rows: int
    size: int

    def __init__(self, arg, rows, columns=None):
        columns = columns or rows
        squares = ((r, c) for r in range(1, rows + 1) for c in range(1, columns + 1))
        if isinstance(arg, str):
            self.string = arg
            self.map = {square: name for square, name in zip(squares, arg) if name != '-'}
        else:
            self.map = arg
            self.string = ''.join(arg.get(square, '-') for square in squares)
        self.rows = rows
        self.columns = columns
        assert len(self.map) % 5 == 0
        assert len(self.map) <= len(self.string) == rows * columns

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.string}", {self.rows}, {self.columns})'

    def __hash__(self) -> int:
        return hash(self.string)

    def __eq__(self, other):
        return self.string == other.string

    @classmethod
    def solve(cls, rows: int, columns: int, holes=Sequence[tuple[int, int]], *,
              show=False):
        results = Pentomino.get_all_pentominos(rows, columns)

        spaces = rows * columns - len(holes)
        assert spaces % 5 == 0

        constraints = {}
        optional_constraints = set()
        for name, cell_list in results.items():
            name_info = f'Shape-{name}'
            for pentomino in cell_list:
                constraints[(name, pentomino)] = [
                    name_info,
                    *[f'r{r}c{c}' for r, c in pentomino]
                ]
            optional_constraints.add(name_info)
        constraints[('-', holes)] = ['Holes', *[f'r{r}c{c}' for r, c in holes]]

        all_tilings = []

        def my_printer(solution):
            mapping = {}
            for name, squares in solution:
                if name != '-':
                    mapping.update((cell, name) for cell in squares)
            tiling = Tiling(mapping, rows, columns)
            all_tilings.append(tiling)
            if show:
                print(tiling)
                tiling.show()

        if spaces == 60:
            optional_constraints.clear()
        solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                              row_printer=my_printer)
        solver.solve(debug=0)

    def show(self, *, axis=None, mapping=None, white: bool = False,
             top_bars=(), left_bars=()):

        shading = {}
        location_to_entry = {}
        color_map = self.__get_color_map()
        for (row, column), name in self.map.items():
            color = color_map[name]
            if not white:
                shading[(row, column)] = color
            if name in mapping:
                location_to_entry[(row, column)] = str(mapping[name])

        draw_grid(axis=axis,
                  max_row=self.rows + 1,
                  max_column=self.columns+1,
                  clued_locations=set(self.map.keys()),
                  location_to_entry=location_to_entry,
                  location_to_clue_numbers={},
                  top_bars=set(top_bars),
                  left_bars=set(left_bars),
                  shading=shading)

    @classmethod
    def show_forced_sharing(cls, tilings, *, top_bars=(), left_bars=()):
        uf = UnionFind()
        squares = list(tilings[0].map.keys())
        for s1, s2 in itertools.combinations(squares, 2):
            if uf.find(s1) != uf.find(s2):
                if all(tiling.map[s1] == tiling.map[s2] for tiling in tilings):
                    uf.union(s1, s2)

        token_map = defaultdict(list)
        for square in squares:
            token_map[uf.find(square)].append(square)

        def extra(plt, _axis):
            for squares in token_map.values():
                if len(squares) > 1 and (2, 2) not in squares:
                    for (r1, c1), (r2, c2) in itertools.combinations(sorted(squares), 2):
                        if r1 == r2 and c2 == c1 + 1:
                            plt.plot((c1 + .5, c2 + .5), (r1 + .5, r2 + .5), linewidth=3,
                                     color='red')
                        elif c2 == c1 and r2 == r1 + 1:
                            plt.plot((c1 + .5, c2 + .5), (r1 + .5, r2 + .5), linewidth=3,
                                     color='red')

        draw_grid(max_row=tilings[0].rows + 1,
                  max_column=tilings[0].columns+1,
                  clued_locations=set(tilings[0].map.keys()),
                  location_to_entry={},
                  location_to_clue_numbers={},
                  top_bars=set(top_bars),
                  left_bars=set(left_bars),
                  extra=extra)

        #
        # intersection_printer(result, 7, 7, top_bars=top_bars, left_bars=left_bars,
        #                      holes=((2, 2), (2, 6), (6, 2), (6, 6)))

    @staticmethod
    @cache
    def __get_color_map():
        colors = ["#C80000", "#9696FF", "#00C8C8", "#FF96FF", "#00C800",
                  "#96FFFF", "#969600", "#C900C0", "#FF9696", "#0000C8", "#FFFF96",
                  "#96FF96"]
        tiles = "FILNPTUVWXYZ"
        return dict(zip(tiles, colors))


if __name__ == '__main__':
    # Tiling.solve(7, 7, ((2, 2), (2, 6), (6, 2), (6, 6)))
    # Tiling.solve(8, 8, ((4, 5), (4, 4), (5, 4), (5, 5)))
    Tiling.solve(5, 12, (), show=True)
