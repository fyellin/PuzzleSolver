import itertools
import multiprocessing
from collections import defaultdict, deque
from collections.abc import Sequence
from contextlib import nullcontext
from datetime import datetime

import math

from misc import Pentomino
from misc.Pentomino import get_graph_colors
from solver import Clues, DancingLinks, EquationSolver

ACROSS_LENGTHS = "213/411/312/213/114/312"
DOWN_LENGTHS = "321/24/213/312/42/123"

class Magpie276(EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.plot_board()

    def __init__(self) -> None:
        clues = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        super().__init__(clues)


PENTOMINOS = {
    "I1": 'X', "I2": 'XX', "I3": "XXX", "L3": 'XX/X.', "I4": 'XXXX',
    "L4": "XXX/X", "O4": 'XX/XX', "S4": ".XX/XX.", "T4": "XXX/.X."
}

class MyPentominos:
    def __init__(self, solver: Magpie276 = None) -> None:
        self.pentominos = Pentomino.Pentomino.all_pentominos(PENTOMINOS)
        self.solver = solver or Magpie276()
        self.my_clue_list = sorted(
            self.solver._clue_list,
            key=lambda x: (-x.is_across, x.length, x.base_location))

    def solve(self, do_check=True, write_file=False, debug=False, **args):
        max_width = max_height = 6

        constraints = {}
        for name, pentominos in self.pentominos.items():
            for pentomino in pentominos:
                for dr in range(1, max_height + 2 - pentomino.height):
                    for dc in range(1, max_width + 2 - pentomino.width):
                        offset_pentomino = pentomino.offset_by(dr, dc)
                        pixels = offset_pentomino.pixels
                        constraint = [name]
                        constraint.extend(f'r{row}c{col}' for (row, col) in pixels)
                        constraints[name, *pixels] = constraint

        # Don't require non-start squares to be tiled. These are the holes filled by 0s
        optional_constraints = {
            f'r{row}c{col}'
            for row in range(1, 7) for col in range(1, 7)
            if not self.solver.is_start_location((row, col))
        }

        my_threes = [
            {f'r{r}c{c}' for (r, c) in [clue.locations[0], clue.locations[-1]]}
            for clue in self.solver._clue_list
            if clue.length == 3 and clue.is_across]
        my_fours = [
            {f'r{r}c{c}' for (r, c) in [clue.locations[0], clue.locations[-1]]}
            for clue in self.solver._clue_list
            if clue.length == 4 and clue.is_across]
        for name, constraint in constraints.items():
            items = set(constraint)
            if any(x <= items for x in my_fours):
                assert name[0] == 'I4'
                constraint.append("pal4")
            if any(x <= items for x in my_threes) and name[0] != 'I4':
                constraint.append(f"pal3-{name[0]}")
        # We've created three primary constraints pal3-I3, pal3-T4, and pal3-L4.
        # We need at least two of them to be true.  To handle this we create a new
        # primary constraint pal3-all-but that takes 0 or 1 of the aforementioned
        # constraints.
        for count in (0, 1):
            for names in itertools.combinations(('I3', 'T4', 'L4'), count):
                constraint = ['pal3-all-but', *(f"pal3-{name}" for name in names)]
                constraints['pal3-all-but', *names] = constraint

        solutions = []

        def handle_solution(solution):
            solutions.append(solution)
            if (count := len(solutions)) % 10_000 == 0:
                print(count)
        solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                              row_printer=handle_solution)
        solver.solve(debug=debug)

        pento_to_letter = dict(zip(self.pentominos.keys(), "ABCDEFGHI", strict=True))

        good_solutions = []
        for solution in solutions:
            grid = {location: piece
                    for piece, *locations in solution for location in locations}
            values = tuple(''.join(pento_to_letter.get(grid.get(location), '0')
                                   for location in clue.locations)
                           for clue in self.my_clue_list)
            if len(values) == len(set(values)):
                good_solutions.append(values)

        # counter = Counter()
        # for solution in solutions:
        #     grid = {location: piece
        #                 for piece, *locations in solution for location in locations}
        #     values = {clue: ''.join(pento_to_letter.get(grid.get(location), '0')
        #               for location in clue.locations)
        #               for clue in self.my_clue_list}
        #     if len(values) == len(set(values.values())):
        #         good_solutions.append(tuple(values.values()))
        #     else:
        #         mydict = defaultdict(list)
        #         for key, value in values.items():
        #             mydict[value].append(key)
        #         for clues in mydict.values():
        #             if len(clues) >= 2:
        #                 key = tuple(clue.name for clue in clues)
        #                 counter[key] += 1
        # print(counter.most_common() )

        bad_count = len(solutions) - len(good_solutions)
        print(f'good={len(good_solutions)} {bad_count=} total={len(solutions)}')
        good_solutions = sorted(set(good_solutions))
        print(f'non-duplicate good={len(good_solutions)}')

        if write_file:
            with open("/tmp/file1", "w") as file:
                for solution in good_solutions:
                    print('.'.join(solution), file=file)
            print("File is written")
        if do_check:
            self.check_everything(good_solutions, **args)

    def draw_solution(self, solution, numbers=None):
        if numbers:
            for digit, letter in zip(numbers, 'ABCDEFGHI'):
                solution = solution.replace(letter, str(digit))
        clue_values = dict(zip(self.my_clue_list, solution.split('.'), strict=True))
        tiles = defaultdict(set)
        for clue, value in clue_values.items():
            for location, letter in zip(clue.locations, value, strict=True):
                if letter != '0':
                    tiles[letter].add(location)

        colors = get_graph_colors(9, False)
        shading = {location: colors[int(digit) - 1]
                   for digit, locations in tiles.items()
                   for location in locations
                   }
        # shading = get_graph_shading(pieces, white=False)
        self.solver.plot_board(clue_values, shading=shading)

    def check_everything(self, good_tilings=None, *, multitasking=True, draw=False):
        if not good_tilings:
            with open("/tmp/file1") as file:
                good_tilings = [line.strip().split('.') for line in file]
        count = 0
        solutions = []
        if multitasking:
            cm = pool = multiprocessing.Pool()
            results = pool.imap(check_all_number_assignments, good_tilings, chunksize=10)
        else:
            cm = nullcontext()
            results = map(check_all_number_assignments, good_tilings)
        with cm:
            for result in results:
                for (line, numbers, letters) in result:
                    count += 1
                    print(line, numbers, letters)
                    if draw:
                        self.draw_solution(line, numbers)
                    solutions.append((line, numbers, letters))

        print(f"Found {count} solutions")
        return solutions


SMALL_FIBO = {13, 21, 34, 55, 89, 144, 233, 377, 610, 987}
SMALL_TRIANGLE = {10, 15, 21, 28, 36, 45, 55, 66, 78, 91}
PALINDROMES = {int(x) for i in range(10, 100)
               for j in [str(i)] for x in (j + j[1] + j[0], j + j[0])}
PRIMES = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73,
          79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157,
          163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239,
          241, 251, 257, 263, 269, 271, 277, 281, 283, 293}


def check_all_number_assignments(items) -> \
        Sequence[tuple[str, Sequence[int], dict[str, int]]]:
    formula = compile_line(items)
    results = []
    for numbers in itertools.permutations(range(1, 10)):
        result = formula(*numbers)
        # result is None if j isn't a palindrome. So we don't need to test that.
        if result is None: continue
        a2, a3, a4, d2, d3, d4 = result

        e, f, g, _h = sorted(a3)
        if e not in PALINDROMES: continue
        if f not in SMALL_FIBO: continue
        if g % e != 0: continue

        a, b, _c, _d = sorted(a2)
        if a not in SMALL_FIBO: continue

        _m, _n, p, _q, r, s = sorted(d2)
        if p not in SMALL_TRIANGLE: continue
        match r:
            case 72: A, C = 3, 2
            case 32: A = C = 2
            case _: continue
        B, remainder = divmod(s, A * A)
        if remainder != 0 or B not in PRIMES: continue
        F, remainder = divmod(b, B)
        if remainder != 0 or F not in PRIMES: continue

        t, _u, _v, w = sorted(d3)
        D, remainder = divmod(t, C * C * F)
        if remainder != 0 or D not in PRIMES: continue
        E = math.isqrt(w // D)
        if E * E * D != w or E not in PRIMES: continue

        x, _y = sorted(d4)
        if (C * D) ** A != x: continue

        results.append(('.'.join(items), numbers, {}))
    return results


def compile_line(items):
    def convert_to_math(word):
        counter = defaultdict(int)
        for index, letter in enumerate(reversed(word)):
            if letter != '0':
                counter[letter] += 10 ** index
        pieces = [f'({letter} * {value})' if value != 1 else letter
                  for letter, value in counter.items()]
        return ' + '.join(pieces)

    # The first letter of the palindrome has to be less than the first letter of the
    # other 4-letter across.  Otherwise, we can fail quickly. "comparison" should be
    # the fail quickly case.
    comparator = '>' if len(set(items[8])) == 1 else '<'
    comparison = f'{items[8][0]} {comparator} {items[9][0]}'

    equations = deque(convert_to_math(item) for item in items)
    equation2 = []
    for i in (4, 4, 2, 6, 4, 2):
        equation2.append('(' + ", ".join(equations.popleft() for _ in range(i)) + ')')
    equation3 = "(" + ", ".join(equation2) + ")"
    equation4 = f"None if {comparison} else {equation3}"
    return eval(f"lambda A,B,C,D,E,F,G,H,I: {equation4}")


TODO = 1

if __name__ == '__main__':
    start = datetime.now()
    match TODO:
        case 1:
            MyPentominos().solve(do_check=False, write_file=False, debug=False)
        case 2:
            MyPentominos().check_everything(multitasking=True, draw=False)

    end = datetime.now()
    print(end - start)

"""
1,423,492,664 x 8
11,387,941,312
17,623,642 -> 2,495,548
   115,674 ->    12,511.   (just Pal4)
     6,729 ->       673.   (Pal4 and Pal3)
"""
