import collections
import itertools
import math
import pickle
from enum import Enum
from typing import Iterable, Optional, Tuple, Sequence, Dict, List, NamedTuple, cast

import numpy as np
from matplotlib import patches as mpatches
from matplotlib import path as mpath
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.backends.backend_pdf import PdfPages

from Clue import Clue, ClueValueGenerator
from ClueList import ClueList
from ClueTypes import ClueValue
from GenericSolver import ConstraintSolver

PDF_FILE_NAME = '/tmp/magpie199.pdf'

VALUE_MAP_PICKLE_FILE = "/tmp/magpie199.dmp"


class Direction(Enum):
    _delta: complex
    _name: str

    Right = ('→', 2 + 0j)
    RightDown = ('↘', 1 + 1j)
    LeftDown = ('↙', -1 + 1j)
    Left = ('←', -2 + 0j)
    LeftUp = ('↖', -1 - 1j)
    RightUp = ('↗', 1 - 1j)

    def __init__(self, name: str, delta: complex) -> None:
        self._name = name
        self._delta = delta

    def __repr__(self) -> str:
        return f'<{self._name}>'

    def delta(self) -> complex:
        return self._delta


class Pentagon(NamedTuple):
    values: Sequence[int]
    directions: Sequence[Direction]

    def get_end_points(self) -> List[Tuple[int, int]]:
        directions = [direction.delta() for direction in self.directions]
        deltas = np.multiply(self.values, directions)
        points = np.cumsum(deltas)
        assert points[-1] == 0
        return [(int(x.real), int(x.imag)) for x in points]

    def get_all_points(self) -> List[Tuple[int, int]]:
        deltas = []
        for value, direction in zip(self.values, self.directions):
            deltas.extend([(direction.delta())] * value)
        points = np.cumsum(deltas)
        assert points[-1] == 0
        return [(int(x.real), int(x.imag)) for x in points]

    def check_no_intersection(self) -> bool:
        points = self.get_all_points()
        return len(set(points)) == sum(self.values)

    def get_size(self) -> int:
        points = self.get_end_points()
        size: int = abs(np.sum(np.cross(points[:-1], points[1:])))
        return size // 2

    def draw_pentagon(self, axes: Axes) -> None:
        points = self.get_end_points()
        points = np.insert(points, 0, [0, 0], axis=0)

        min_x, min_y = np.amin(points, axis=0)
        max_x, max_y = np.amax(points, axis=0)

        axes.axis([min_x - .5, max_x + .5, max_y + .5, min_y - .5])
        axes.set_aspect('1.7')
        axes.axis('off')

        path = mpath.Path(points, closed=True)
        patch = mpatches.PathPatch(path, facecolor='white', lw=1)
        axes.add_patch(patch)

        test_points = [(x, y + .5) for y in range(min_y - 2, max_y + 2)
                       for x in range(min_x - 1, max_x + 2)]
        test_results = path.contains_points(test_points)
        triangle_points = [(x, math.floor(y)) for ((x, y), result) in zip(test_points, test_results) if result]
        assert len(triangle_points) == self.get_size()
        for i, (x, y) in enumerate(triangle_points, start=1):
            fontsize = 6 if i >= 100 else 8
            if (x + y) % 2 == 1:
                axes.plot([x - 1, x + 1, x, x - 1], [y, y, y + 1, y], lw=0.5, color='black')
                axes.text(x, y + .3, str(i), fontsize=fontsize, fontweight='bold', va='center', ha='center')
            else:
                # We only need to draw half the triangles.  The three sides of every triangle are either a triangle
                # pointing the other way, or the border.
                # axes.plot([x - 1, x + 1, x, x - 1], [y + 1, y + 1, y, y + 1], lw=0.5, color='black')
                axes.text(x, y + .7, str(i), fontsize=fontsize, fontweight='bold', va='center', ha='center')

        all_points = self.get_all_points()
        x_points, y_points = list(zip(*all_points))
        axes.plot(x_points, y_points, "bh")  # black hexagonal.  A hexagon seems appropriate!

        for (x1, y1), (x2, y2), length in zip(points, points[1:], self.values):
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            slope = (y2 - y1) / (x2 - x1)
            magnitude = math.sqrt(slope * slope + 1)
            offset_x, offset_y = .4 * slope / magnitude, .4 * -1.0 / magnitude

            if path.contains_point((mid_x + offset_x, mid_y + offset_y)):
                offset_x, offset_y = -offset_x, -offset_y
            axes.text(mid_x + offset_x, mid_y + offset_y, str(length), color='red', size='large',
                      va='center', ha='center')


ClueMap = Dict[int, List[Pentagon]]


def generate_map() -> ClueMap:
    accepted = 0
    rejected = 0
    result: ClueMap = collections.defaultdict(list)
    direction_list = [x for x in Direction]
    lengths = [v for v in itertools.permutations(range(1, 10), 5) if v[0] == min(v) and v[1] < v[4]]
    right_turns = list(x for x in itertools.product([0], [1, 2], [1, 2, 4, 5], [1, 2, 4, 5], [1, 2, 4, 5])
                       if sum(x) % 3 != 0)
    total_turns = np.cumsum(right_turns, axis=1) % 6
    turn_vectors = np.choose(total_turns, [x.delta() for x in Direction])
    length_direction_total_path_vector = np.inner(lengths, turn_vectors)

    length_indices_where_zero, direction_indices_where_zero = np.where(length_direction_total_path_vector == 0)
    for length_index, direction_index in zip(length_indices_where_zero, direction_indices_where_zero):
        length, direction = lengths[length_index], np.choose(total_turns[direction_index], direction_list)
        pentagon = Pentagon(length, direction)
        if pentagon.check_no_intersection():
            size = pentagon.get_size()
            result[size].append(pentagon)
            accepted += 1
        else:
            rejected += 1
    print(f'Accepted:{accepted}, Rejected:{rejected}')
    return result


ACROSS = (('a', 135), ('c', 48), ('f', 107), ('g', 87), ('h', 81),
          ('j', 125), ('m', 75), ('n', 51), ('o', 30), ('p', 21))

DOWNS = (('a', 17), ('b', 90), ('c', 85), ('d', 71), ('e', 27),
         ('h', 140), ('i', 63), ('j', 44), ('k', 99), ('l', 77))


def make_clue_list(clue_map: ClueMap) -> ClueList:
    def generator(clue_value: int) -> ClueValueGenerator:
        def result(_: Clue) -> Iterable[str]:
            values_list = [v for (v, _) in clue_map[clue_value]]
            for values in values_list:
                string = ''.join(map(str, values))
                for i in range(5):
                    temp = ''.join(string[i:] + string[:i])
                    yield temp
                    yield temp[::-1]
        return result

    clues = []
    for (letter, value), location in zip(ACROSS, itertools.product((1, 3, 5, 7, 9), (1, 5))):
        clues.append(Clue(letter.upper(), True, location, 5, context=value, generator=generator(value)))
    for (letter, value), location in zip(DOWNS, itertools.product((1, 5), (1, 3, 5, 7, 9))):
        clues.append(Clue(letter, False, location, 5, context=value, generator=generator(value)))
    clue_list = ClueList(clues)
    return clue_list


class MySolver(ConstraintSolver):
    clue_map: ClueMap

    def __init__(self, clue_list: ClueList, clue_map: ClueMap):
        super().__init__(clue_list)
        self.clue_map = clue_map

    def check_and_show_solution(self, known_clues: Dict[Clue, ClueValue]) -> None:
        all_clues = collections.deque(self.clue_list)
        with PdfPages(PDF_FILE_NAME) as pdf:
            figure, axis = plt.subplots(1, 1, figsize=(8, 11), dpi=100)
            self.clue_list.plot_board(known_clues, axes=axis)
            pdf.savefig()
            plt.close()

            while all_clues:
                figure, axes = plt.subplots(2, 2, figsize=(8, 11), dpi=100)
                for i in range(4):
                    if all_clues:
                        self.draw_clue_pentagon(all_clues.popleft(), known_clues, axes[divmod(i, 2)])
                pdf.savefig(figure)
                plt.close()
            print(f"Finished writing to {PDF_FILE_NAME}")

    def draw_clue_pentagon(self, clue: Clue, known_clues: Dict[Clue, ClueValue], axes: Axes) -> None:
        triangles = cast(int, clue.context)
        answer = known_clues[clue]
        canonical_answer = min(answer[i:] + answer[:i] for i in range(5))
        if canonical_answer[1] > canonical_answer[-1]:
            canonical_answer = canonical_answer[0] + canonical_answer[1:][::-1]
        canonical_lengths = tuple(map(int, list(canonical_answer)))
        pentagon = next(p for p in self.clue_map[triangles] if p.values == canonical_lengths)
        pentagon.draw_pentagon(axes)
        axes.set_title(f'{clue.name}: {triangles} = {answer}')


def get_dumped_map() -> ClueMap:
    with open(VALUE_MAP_PICKLE_FILE, "rb") as file:
        return cast(ClueMap, pickle.load(file))


def run(clue_map: Optional[ClueMap] = None) -> None:
    clue_map = clue_map or get_dumped_map()
    clue_list = make_clue_list(clue_map)
    clue_list.verify_is_four_fold_symmetric()
    solver = MySolver(clue_list, clue_map)
    solver.solve(debug=False)


def build(dump: bool = False) -> None:
    value_map = generate_map()
    if dump:
        with open(VALUE_MAP_PICKLE_FILE, "wb") as file:
            pickle.dump(value_map, file)
    else:
        assert value_map == get_dumped_map()


if __name__ == '__main__':
    build(True)
    run()
