from collections import defaultdict

import itertools
import time
from operator import itemgetter
from typing import Any, Callable, Sequence

from solver import Clue, Clues, ConstraintSolver

GRID = """
XXX.XX.X
X..X.XX.
X..X...X
X...XX..
XX.XX...
..X...X.
X...X..X
X...X...
"""

ACROSS_LENGTHS = ((1, 4), (4, 4), (7, 4), (9, 3), (11, 2), (12, 3), (14, 4), (15, 4),
                  (17, 4), (20, 4), (21, 3), (22, 2), (23, 3), (24, 4), (26, 4), (27, 4))

DOWN_LENGTHS = ((1, 2), (11, 4), (23, 2), (2, 3), (18, 3), (3, 5), (21, 3), (8, 3),
                (19, 4), (4, 4), (20, 3), (5, 3), (16, 5), (10, 3), (22, 3), (6, 2),
                (13, 4), (25, 2))

Unclued = object()

CLUES = [
    28, 43, 73, 219, 45, 93, 29, 213, 135, 123, 215, 615, 713, 192, 226, 623, 513,
    2312, 549, 4112, Unclued, Unclued, 1413, 1115, 717, 855, 6136, 7103, 727, 1622,
    1124, 4614, Unclued, 3157]


class Magpie257(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.verify_is_180_symmetric()
        solver.solver()

    def __init__(self) -> None:
        clues = self.get_clues()
        assert len(clues) == len(CLUES)
        super().__init__(clues)

    def get_clues(self) -> Sequence[Clue]:
        clues = []
        locations = Clues.get_locations_from_grid(GRID)
        for clue_list in (ACROSS_LENGTHS, DOWN_LENGTHS):
            is_across = clue_list == ACROSS_LENGTHS
            for number, length in clue_list:
                clue = Clue(f'{number}{'a' if is_across else 'd'}', is_across,
                            locations[number - 1], length)
                clues.append(clue)
        return clues

    def solver(self):
        known_clues = {}
        board = [None] * 64
        steps = 0
        solutions = 0
        clue_locations = {clue: [r * 8 + c - 9 for (r, c) in clue.locations]
                          for clue in self._clue_list}
        zero_locations = {r * 8 + c - 9 for r in range(1, 9) for c in range(1, 9)
                          if self.is_start_location((r, c))}

        def get_clue_value(last_value: str, possible_values: Sequence[str],
                           possible_clues: Sequence[Clue],
                           next_function: Callable, next_args: tuple[Any, ...]):
            for possible_value in possible_values:
                if possible_value >= last_value:
                    for clue in possible_clues:
                        if clue not in known_clues:
                            fill_in_grid(clue, possible_value, next_function, next_args)

        def fill_in_grid(clue: Clue, possible_value: str,
                         next_function: Callable, next_args: tuple[Any, ...]):
            nonlocal steps
            steps += 1
            locations_set = []
            for location, char in zip(clue_locations[clue], possible_value):
                if (old_char := board[location]) is not None:
                    if char != old_char:
                        break
                else:
                    if char == '0' and location in zero_locations:
                        break
                    board[location] = char
                    locations_set.append(location)
            else:
                # We end up here if we never performed a "break"
                known_clues[clue] = possible_value
                next_function(possible_value, *next_args)
                del known_clues[clue]

            for location in locations_set:
                board[location] = None

        def reset_last_value(_last_value: str, next_function: Callable, next_args: tuple[Any, ...]):
            next_function("", *next_args)

        def init_finish_puzzle():
            nonlocal known_clues
            clue_values = [3479, None, 6336, 450, 32, 325, 5047, 5103, 2775, 9016, 162,
                           76, 828, 4896, 1792, None, 36, 3520, 81, 432, 722, 73947, 189,
                           637, 5632, 1225, 924, 845, None, 540, 792, 80, 2366, 63]
            clue_values = [str(value) if value else None for value in clue_values]
            known_clues |= {clue: value for clue, value in
                            zip(self._clue_list, clue_values) if value}
            for clue, value in known_clues.items():
                for (x, y), letter in zip(clue.locations, value):
                    board[x][y] = letter

        def finish_puzzle(*_args):
            if not known_clues:
                init_finish_puzzle()
            clues = [clue for clue in self._clue_list if clue not in known_clues]
            assert len(clues) == 3
            range4 = range(1793, 2366)   #19, 20
            range5 = range(10000, 73947)
            ranges = [range4 if clue.length == 4 else range5 for clue in clues]
            for i in range(3):
                step1(*clues, *ranges)
                clues.append(clues.pop(0))
                ranges.append(ranges.pop(0))

        def step1(clue_a, clue_b, clue_c, range_a, range_b, range_c):
            for value in range_a:
                fill_in_grid(clue_a, str(value), step2, (clue_b, clue_c, range_b, range_c))

        def step2(value, clue_b, clue_c, range_b, range_c):
            possible_values = get_possible_values(value, clue_b.length)
            for next_value in possible_values:
                if next_value in range_b:
                    fill_in_grid(clue_b, str(next_value), step3, (value, clue_c, range_c))

        def step3(_, value, clue_c, range_c):
            possible_values = get_possible_values(value, clue_c.length)
            for next_value in possible_values:
                if next_value in range_c:
                    fill_in_grid(clue_c, str(next_value), print_result, ())

        def print_result(*_args):
            nonlocal solutions
            solutions += 1
            self.show_solution(known_clues)

        def get_runner():
            clue_by_length = defaultdict(list)
            for clue in self._clue_list:
                clue_by_length[clue.length].append(clue)

            sorted_lengths = sorted(clue.length for clue in self._clue_list)
            clue_triples = [(clue, length, get_possible_values(clue, length))
                            for clue, length in zip(CLUES, sorted_lengths)
                            if clue is not Unclued]
            changed = True
            while changed:
                changed = False
                for (_, _, values1), (_, _, values2) in itertools.pairwise(clue_triples):
                    while values2[0] <= values1[0]:
                        values2.pop(0); changed = True
                    while values1[-1] >= values2[-1]:
                        values1.pop(); changed = True
            # steps = [(get_clue_value, (possible_values, clue_by_length[length]))
            #          for (number, length, possible_values) in reversed(clue_triples)]
            triples_by_length = {}
            for key, values in itertools.groupby(clue_triples, key=itemgetter(1)):
                triples_by_length[key] = list(values)
            steps = []
            for length in (3, 2, 4, 5):
                steps.append((reset_last_value, ()))
                for number, _, possible_values in triples_by_length[length]:
                    temp = [str(x) for x in possible_values]
                    steps.append((get_clue_value, (temp, clue_by_length[length])))
            steps.append((finish_puzzle, ()))
            current_function, current_args = (lambda *x: None), None
            for (func, args) in reversed(steps):
                current_args = (*args, current_function, current_args)
                current_function = func
            return lambda: current_function(None, *current_args)

        def get_possible_values(number, length):
            values = set()
            number = str(number)
            for i in range(1, len(number)):
                left, right = int(number[0:i]), int(number[i:])
                for value in (left * left * right, left * right * right):
                    if len(str(value)) == length:
                        values.add(value)
            return sorted(values)

        runner = get_runner()
        start = time.perf_counter_ns()
        runner()
        # finish_puzzle(None, None)
        end = time.perf_counter_ns()
        print(f'{(end - start) / 1_000_000_000:3f}s; {steps:,} steps; {solutions} solution(s)')


if __name__ == '__main__':
    Magpie257.run()
