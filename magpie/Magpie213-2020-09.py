import datetime
import functools
import itertools
import math
import re
from collections import defaultdict, Counter
from collections.abc import Sequence
from typing import cast, Any

from matplotlib import pyplot as plt
from matplotlib.patches import Ellipse

from solver import generators, ConstraintSolver, Clues, Clue, Location


def make_min_max_factor_table() -> Sequence[tuple[int, int]]:
    primes = tuple(itertools.takewhile(lambda x: x < 315, generators.prime_generator()))
    primes_set = set(primes)
    min_max_factor = [(0, 0)] * 100000
    min_max_factor[1] = (1, 1)
    for value in range(2, len(min_max_factor)):
        if value % 10000 == 0:
            print(value)
        if value in primes_set:
            min_max_factor[value] = (value, value)
        else:
            factor = next((x for x in primes if value % x == 0), None)
            if not factor:
                min_max_factor[value] = (value, value)
            else:
                fmin, fmax = min_max_factor[value // factor]
                min_max_factor[value] = min(fmin, factor), max(fmax, factor)
    return min_max_factor


@functools.lru_cache(None)
def make_puzzle_table() -> dict[tuple[int, int], Sequence[int]]:
    result: dict[tuple[int, int], list[int]] = defaultdict(list)
    min_max_factor_table = make_min_max_factor_table()
    for length in range(2, 6):
        for value in range(10 ** (length - 1), 10 ** length):
            fmin, fmax = min_max_factor_table[value]
            if value != fmin:  # not a prime
                result[length, fmax - fmin].append(value)
    return result


GRID = """
X...xxx..x....x
...x.x.x.x...
.x.xx.xx.xx
...xxx..x
xx.x.x.
x....
...
x
"""

HARVEST = """
7 1872 (4)
9 65 (4)
11 412 (4)
17 8884 (5)
18 2 (4)
19 0 (4) 
21 2716 (4) 
23 0 (4)
27 500 (5)
"""

INUNDATION = """
1 194 (5) 
3 3 (4) 
5 39 (4) 
8 294 (4)
10 116 (4)
13 3034 (4)
20 0 (4)
22 14 (4)
26 2374 (5)
"""

PLANTING = """
2 30 (5) 
4 0 (4)
6 27579 (5)
12 4077 (4)
14 2 (4)
15 0 (4) 
16 0 (4) 
24 177 (4) 
25 5 (4) 
"""


class Solver213(ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Solver213()
        solver.solve()

    @staticmethod
    def test() -> None:
        answers = {'6p': 55162, '17h': 26661, '10i': 7661, '12p': 8158, '13i': 9111, '14p': 1125, '18h': 5183,
                   '19h': 2197, '21h': 8157, '16p': 1849, '20i': 2048, '15p': 1024, '23h': 6859, '5i': 5166,
                   '7h': 9385, '1i': 82585, '2p': 58339, '11h': 2933, '8i': 7291, '9h': 9246, '3i': 8640, '22i': 8619,
                   '24p': 9666, '26i': 16667, '27h': 82661, '25p': 1764, '4p': 6889}
        solver = Solver213()
        known_clues = {solver.clue_named(clue): str(value) for clue, value in answers.items()}
        solver.plot_board(known_clues)

    def __init__(self) -> None:
        super().__init__(self.get_clue_list())

    @staticmethod
    def get_clue_list() -> Sequence[Clue]:
        grid_locations = Clues.get_locations_from_grid(GRID)

        def generator(clue: Clue) -> Sequence[int]:
            length = clue.length
            delta = cast(int, clue.context)
            return make_puzzle_table()[length, delta]

        clues = []
        for lines, is_across, letter in ((INUNDATION, True, 'i'), (HARVEST, False, 'h'), (PLANTING, False, 'p')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (\d+) \((\d+)\)', line)
                assert match
                number, delta, length = int(match.group(1)), int(match.group(2)), int(match.group(3))
                (row, column) = grid_locations[number - 1]
                if letter == 'i':
                    locations = [(row, column + i) for i in range(length)]
                elif letter == 'h':
                    locations = [(row, column)]
                    while len(locations) < length:
                        row, column = (row, column - 1) if column % 2 == 0 else (row - 1, column + 1)
                        locations.append((row, column))
                else:
                    locations = [(row, column)]
                    while len(locations) < length:
                        row, column = (row, column - 1) if column % 2 == 1 else (row + 1, column - 1)
                        locations.append((row, column))
                clue = Clue(f'{number}{letter}', is_across, (row, column), length,
                            locations=locations, context=delta, generator=generator)
                clues.append(clue)
        return clues

    def draw_grid(self, *,
                  location_to_entry: dict[Location, str],
                  location_to_clue_numbers: dict[Location, Sequence[str]], **args: Any) -> None:
        _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)
        # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
        axes.axis([1, 9, 9, 1])
        aspect_ratio = math.sqrt(3)/2
        axes.set_aspect(aspect_ratio)
        axes.axis('off')

        def draw_heavy(row, column, where: str | tuple[str, str], color: str = 'black'):
            is_point_up = column % 2 == 0
            point_row, flat_row = (row, row + 1) if is_point_up else (row + 1, row)
            center_x = (1 + row + column) / 2.0
            if isinstance(where, tuple):
                where = where[0] if is_point_up else where[1]
            args = dict(color=color, linewidth=5)
            if where == 'left':
                if column != 1:
                    axes.plot([center_x, center_x - .5], [point_row, flat_row], **args)
            elif where == 'right':
                if column + 2 * row != 17:
                    axes.plot([center_x, center_x + .5], [point_row, flat_row], **args)
            elif where in ('top', 'bottom'):
                if is_point_up or row != 1:
                    axes.plot([center_x - .5, center_x + .5], [flat_row, flat_row], **args)


        text_args = dict(verticalalignment='center', horizontalalignment='center',
                         fontsize=20, fontfamily="sans-serif", fontweight='bold')

        label_args = dict(fontsize=10, fontfamily="sans-serif", fontweight='bold')
        for (row, column), value in location_to_entry.items():
            label = location_to_clue_numbers.get((row, column))
            center_x = (1 + row + column) / 2.0
            if column % 2 == 1:
                axes.plot([center_x, center_x - .5, center_x + .5, center_x], [row + 1, row, row, row + 1],
                          color='black')
                axes.text(center_x, row + .6, value, **text_args)
                if label:
                    axes.text(center_x - .4, row + .05, str(label[0]),
                              verticalalignment='top', horizontalalignment='left', **label_args)
            else:
                axes.plot([center_x, center_x - .5, center_x + .5, center_x], [row, row + 1, row + 1, row],
                          color='black')
                axes.text(center_x, row + .7, value, **text_args)
                if label:
                    axes.text(center_x, row + .15, str(label[0]),
                              verticalalignment='top', horizontalalignment='center', **label_args)
        radius = 1.5
        axes.add_patch(Ellipse((2.5, 2), radius, radius/aspect_ratio, color="#fde2c8"))
        axes.add_patch(Ellipse((7.5, 2), radius, radius/aspect_ratio, color="#fde2c8"))
        axes.add_patch(Ellipse((5.0, 7), radius, radius/aspect_ratio, color="#fde2c8"))

        for clue in self._clue_list:
            if clue.name.endswith("i"):
                draw_heavy(*clue.locations[0], 'left')
                draw_heavy(*clue.locations[-1], 'right')
            elif clue.name.endswith("h"):
                draw_heavy(*clue.locations[0], ('bottom', 'right'))
                draw_heavy(*clue.locations[-1], ('left', 'top'))
            elif clue.name.endswith("p"):
                pass
                draw_heavy(*clue.locations[0], ('right', 'top'))
                draw_heavy(*clue.locations[-1], ('bottom', 'left'))
        draw_heavy(1, 10, 'bottom')
        draw_heavy(3, 2, 'right')
        draw_heavy(5, 5, 'right')

        plt.show()


def foobar(x) -> None:
    all_items = {''.join(values) for values in itertools.permutations(str(x))}
    weights = sorted(int(x) for x in all_items)
    print('*******')
    for weight in weights:
        net = weight * 4 / 33333
        inet = round(net)
        expected_weight = inet * 33333 / 4
        if abs(expected_weight - weight) < 5:
            print(weight, inet, expected_weight, expected_weight - weight)


def hanoi() -> None:
    count = 0
    piles = [[7], [6, 5, 4, 3, 2, 1], []]
    result = Counter()

    def move(stone: int, start: int, end: int) -> None:
        nonlocal count
        assert stone == piles[start][-1]
        assert stone < (piles[end][-1] if piles[end] else 1000)
        piles[start].pop()
        if stone == 1:
            temp = 3 - start - end
            piles[temp].append(stone)
            favorite = max(pile[-1] for pile in piles if pile)
            piles[temp].pop()
            result[favorite] += 1
        else:
            favorite = None
        piles[end].append(stone)
        count += 1
        print(f'{count:3}: {stone}:{start+1}->{end+1}:    '
              f'{xx(piles[0]):7} {xx(piles[1]):7}  {xx(piles[2]):7} {favorite}')

    def internal(count: int, start: int, end: int) -> None:
        temp = 3 - start - end
        if count > 1:
            internal(count - 1, start, temp)
        move(count, start, end)
        if count > 1:
            internal(count - 1, temp, end)

    def xx(pile: Sequence[int]) -> str:
        return ''.join(str(x) for x in sorted(pile, reverse=True))

    move(7, 0, 2)
    internal(6, 1, 2)
    internal(6, 2, 0)
    print(result)

"""
Generator: 0:00:00.055020; list: 0:00:00.092192
Generator: 0:00:12.039189; list: 0:00:00.363289

"""
def sum_with_list():
    return sum([i * i for i in range(1, 1_000_000)])

def sum_with_generator():
    return sum(i * i for i in range(1, 1_000_000))

def test():
    time1 = datetime.datetime.now()
    print(sum_with_generator())
    time2 = datetime.datetime.now()
    print(sum_with_list())
    time3 = datetime.datetime.now()
    print(f'Generator: {time2 - time1}; list: {time3 - time2}')

if __name__ == '__main__':
    Solver213().run()
