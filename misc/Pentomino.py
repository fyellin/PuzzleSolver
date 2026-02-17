from itertools import combinations
from typing import NamedTuple

import matplotlib

from solver import DancingLinks

PENTOMINOS = dict(
    F='.XX/XX./.X.', I='XXXXX', L="XXXX/X...", N='XX/.XXX', P='XXX/XX',
    T="XXX/.X/.X", U="X.X/XXX", V="XXX/X/X", W="..X/.XX/XX", X=".X./XXX/.X.",
    Y="XXXX/.X", Z="XX/.X/.XX"
)


class Pentomino(NamedTuple):
    pixels: tuple[tuple[int, int], ...]
    width: int
    height: int

    @staticmethod
    def from_picture(picture: str):
        picture = picture.split('/')
        height = len(picture)
        width = max(len(line) for line in picture)
        pixels = [(row, column)
                  for row, line in enumerate(picture)
                  for column, ch in enumerate(line) if ch == 'X']
        return Pentomino(tuple(sorted(pixels)), width=width, height=height)

    def rotate_right(self):
        result = tuple(sorted((col, self.height - 1 - row) for (row, col) in self.pixels))
        return Pentomino(result, width=self.height, height=self.width)

    def mirror(self):
        result = tuple(sorted((row, self.width - 1 - col) for (row, col) in self.pixels))
        return Pentomino(result, width=self.width, height=self.height)

    def offset_by(self, dr, dc):
        result = tuple(sorted((row + dr, col + dc) for (row, col) in self.pixels))
        return Pentomino(result, width=self.width, height=self.height)

    @staticmethod
    def all_pentominos(pictures=None, mirror=True):
        pictures = pictures or PENTOMINOS
        result = {}
        for letter, picture in pictures.items():
            picture1 = Pentomino.from_picture(picture)
            picture2 = picture1.rotate_right()
            picture3 = picture2.rotate_right()
            picture4 = picture3.rotate_right()
            pictures = {picture1, picture2, picture3, picture4}
            if mirror:
                pictures |= {picture.mirror() for picture in pictures}
            result[letter] = pictures
        return result

class PentominoSolver:
    def solve(self, max_width: int, max_height: int, predicate, *,
              all_pentominos=None,
              debug=False
              ) -> list[dict[str, tuple[tuple[int, int], ...]]]:

        constraints = {}
        all_pentominos = all_pentominos or Pentomino.all_pentominos()
        for letter, pentominos in all_pentominos.items():
            count = 0
            for pentomino in pentominos:
                for dr in range(0, max_height + 2 - pentomino.height):
                    for dc in range(0, max_width + 2 - pentomino.width):
                        offset_pentomino = pentomino.offset_by(dr, dc)
                        pixels = offset_pentomino.pixels
                        if predicate(pixels):
                            count += 1
                            constraint = [letter]
                            constraint.extend(f'r{row}c{col}' for (row, col) in pixels)
                            constraints[(letter, *pixels)] = constraint
            if count == 0:
                print(f"No location to put letter '{letter}' in grid")
                return []

        results = []

        def my_printer(solution):
            nonlocal results
            results.append({color: squares for (color, *squares) in solution})

        solver = DancingLinks(constraints, row_printer=my_printer)
        solver.solve(debug=debug)
        return results


def get_graph_shading(solution, colors=None, white=True):
    from networkx import Graph, greedy_color
    # Figure out a nice coloring for the pentominos, so that we use a
    # minimum number of colors, but adjacent pentominos are different colors
    graph = Graph()
    if not isinstance(solution, dict):
        solution = dict(enumerate(solution))
    graph.add_nodes_from(key for key in solution)
    for (key1, squares1), (key2, squares2) \
            in combinations(solution.items(), 2):
        # Make a path between two nodes if they're touching, even diagonally
        if any(abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1
               for (r1, c1) in squares1 for (r2, c2) in squares2):
            graph.add_edge(key1, key2)
    color_assignment = greedy_color(graph)
    if colors is None:
        color_count = max(color_assignment.values()) + 1
        colors = get_graph_colors(color_count, white)

    shading = {square: color
               for letter, squares in solution.items()
               for color in [colors[color_assignment[letter]]]
               for square in squares}
    return shading


def get_graph_colors(color_count: int, white=True):
    if white:
        colors = [matplotlib.colors.hsv_to_rgb((i / color_count, .6, 1))
                  for i in range(color_count - 2)] + [(1, 1, 1), (.7, .7, .7)]
    else:
        colors = [matplotlib.colors.hsv_to_rgb((i / color_count, .6, 1))
                  for i in range(color_count - 1)] + [(.7, .7, .7)]
    return colors


def get_hard_bars(solution):
    if not isinstance(solution, dict):
        solution = dict(enumerate(solution))
    location_to_key = {location: key for key, locations in solution.items()
                       for location in locations}
    min_row = min(x for x, _ in location_to_key.keys())
    max_row = max(x for x, _ in location_to_key.keys()) + 1
    min_column = min(y for _, y in location_to_key.keys())
    max_column = max(y for _, y in location_to_key.keys()) + 1
    # Location of squares that have a heavy bar on their left.
    left_bars = {(r, c)
                    for r in range(min_row, max_row)
                    for c in range(min_column + 1, max_column)
                    if location_to_key.get((r, c)) != location_to_key.get((r, c - 1))}
    top_bars = {(r, c)
                   for r in range(min_row + 1, max_row)
                   for c in range(min_column, max_column)
                   if location_to_key.get((r, c)) != location_to_key.get((r - 1, c))}
    return left_bars, top_bars
