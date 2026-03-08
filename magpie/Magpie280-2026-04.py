import string
from collections.abc import Sequence
from functools import cache
from itertools import count
from typing import Any, Unpack, override

from more_itertools import is_sorted

from solver import (
    Clue,
    Clues,
    DancingLinksSolver,
    DrawGridKwargs,
    EquationParser,
    KnownClueDict,
)
from solver.dancing_links import DLConstraint

ACROSS_LENGTHS = "44/2132/143/341/2312/44"
DOWN_LENGTHS = "141/33/42/24/42/24/33/141"

# ruff: noqa: RUF001
CLUES = """
1 AB
2 D
3 2A + 2C
4 B(C − A)
5 A + 3AB
6 A(B + D)
7 12B − A − C
8 6A + D + F
9 2A + C + E + H
10 3A + F + H
11 B(C − A)(D − C)
12 2J − 4A
13 L − 2A
14 L + 2A
15 EF
16 4J − B − D
17 E + M
18 12H − E
19 F + FF + K
20 B + G + N
21 FG + K
22 5A + 7K − J
23 F + P − A − 6G
24 4M − BC
25 4M − D
26 L + P − 2E
27 2A + C + H + 8L
28 Q − C − N
"""


class Magpie280(DancingLinksSolver):
    @classmethod
    def run(cls) -> None:
        solver = cls()
        solver.verify_is_180_symmetric()
        solver.solve(debug=False)

    def __init__(self) -> None:
        run_information = GetBasicInfo().get_run_information()
        assert len(run_information) == 1
        self.fibonacci, values = run_information[0]
        clues = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        self.values = [str(x) for x in values]
        for clue in clues:
            clue.generator = self.my_generator
        super().__init__(clues)

    def my_generator(self, clue: Clue):
        length = clue.length
        for value in self.values:
            if len(value) == length:
                yield value
            elif len(value) == length - 1:
                for i in range(0, len(value) + 1):
                    yield value[:i] + ' ' + value[i:]

    @override
    def get_clue_value_constraints(self, clue: Clue, value: Any,
                                   optional_constraints: set[str]) -> Sequence[DLConstraint]:
        result = list(super().get_clue_value_constraints(clue, value, optional_constraints))
        if ' ' not in value:
            real_value = value
        else:
            space_index = value.index(' ')
            r, c = clue.locations[space_index]
            optional_constraints.add("space")
            result.append(("space", f"r{r}c{c}"))
            real_value = value[:space_index] + value[space_index + 1:]
        result.append(f"value={real_value}")
        return result

    def draw_grid(self, **kwargs: Unpack[DrawGridKwargs]) -> None:
        clue_values = kwargs['clue_values']
        kwargs['location_to_clue_numbers'].clear()
        line = self.get_line(clue_values)

        location_to_entry = kwargs['location_to_entry']
        location_to_entry[line[0]] = str(self.fibonacci[0])
        import numpy as np
        points = np.array(line)

        def extra(_plt, axes):
            axes.plot(points[:, 1] + .5, points[:, 0] + .5, color='blue', alpha=.5, linestyle=":")

        super().draw_grid(shading={line[-1]: 'red'},
                          # coloring={line[0]: 'blue'},
                          # extra=extra,
                          **kwargs)

    def get_line(self, clue_values: KnownClueDict):
        board = self.get_board(clue_values)
        target = ''.join(map(str, self.fibonacci))
        results = []

        def next_step(path):
            if len(path) == 48:
                results.append(path)
                return
            (row, column) = path[-1]
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                temp = (row + dr, column + dc)
                if temp not in path and board.get(temp) == target[len(path)]:
                    next_step((*path, temp))

        next_step(((3, 4),))
        result, = results
        return result


class GetBasicInfo:
    def __init__(self):
        self.equation = self.get_equation()

    @staticmethod
    @cache
    def get_equation():
        parser = EquationParser()
        pieces = [
            parser.parse(piece)[0].to_string()
            for line in CLUES.strip().splitlines()
            for piece in [line.split(' ', 1)[1]]]
        alphabet = string.ascii_uppercase[:18]
        equation = f"lambda {','.join(alphabet)}: ({", ".join(pieces)})"
        return eval(equation)

    def get_information_for(self, i, j):
        fib = [i, j]
        while len(fib) < 18:
            fib.append(fib[-1] + fib[-2])
        length = sum(len(str(i)) for i in fib)
        return length, fib, self.equation(*fib)

    def get_run_information(self) -> list[tuple[Sequence[int], Sequence[int]]]:
        results = []
        for i in count(1):
            for j in count(1):
                length, fib, result = self.get_information_for(i, j)
                if length > 48 or result[-1] > 9999:
                    if j == 1:
                        return results
                    break
                if length == 48 and is_sorted(result, strict=True):
                    results.append((fib, result))
        raise ValueError("No solution found")

    def foobar(self):
        for i in range(-10, 10):
            for j in range(-10, 10):
                length, fib, result = self.get_information_for(i, j)
                if length == 48 and is_sorted(result, strict=True):
                    print(i, j, length, fib, result)


if __name__ == '__main__':
    Magpie280.run()
