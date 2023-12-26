from typing import NamedTuple

from solver import DancingLinks

PENTOMINOS = dict(
    F='.XX/XX./.X.', I='XXXXX', L="XXXX/X...", N='XX/.XXX', P='XXX/XX',
    T="XXX/.X/.X", U="X.X/XXX", V="XXX/X/X", W="..X/.XX/XX", X=".X./XXX/.X.",
    Y="XXXX/.X", Z="XX/.X/.XX"
)

class Pentomino(NamedTuple):
    pixels: tuple[tuple[int, int]]
    width: int
    height: int

    @staticmethod
    def from_picture(picture: str):
        assert picture.count('X') == 5
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
    def all_pentominos():
        result = {}
        for letter, picture in PENTOMINOS.items():
            picture1 = Pentomino.from_picture(picture)
            picture2 = picture1.rotate_right()
            picture3 = picture2.rotate_right()
            picture4 = picture3.rotate_right()
            pictures = {picture1, picture2, picture3, picture4}
            pictures |= {picture.mirror() for picture in pictures}
            result[letter] = pictures
        return result

class PentominoSolver:
    def solve(self, max_width: int, max_height: int, predicate, *, debug=False
              ) -> dict[str, tuple[tuple[int, int], ...]]:
        constraints = {}
        all_pentominos = Pentomino.all_pentominos()
        for letter, pentominos in all_pentominos.items():
            for pentomino in pentominos:
                for dr in range(0, max_height + 2 - pentomino.height):
                    for dc in range(0, max_width + 2 - pentomino.width):
                        offset_pentomino = pentomino.offset_by(dr, dc)
                        pixels = offset_pentomino.pixels
                        if predicate(pixels):
                            constraint = [letter]
                            constraint.extend(f'r{row}c{col}' for (row, col) in pixels)
                            constraints[(letter, *pixels)] = constraint

        results = []

        def my_printer(solution):
            nonlocal results
            results.append({color: squares for (color, *squares) in solution})

        solver = DancingLinks(constraints, row_printer=my_printer)
        solver.solve(debug=debug)
        return results
