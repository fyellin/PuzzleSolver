import collections
import itertools
import math
import pickle
from enum import Enum
from typing import Iterable, Optional, Tuple, Sequence, Dict, List, NamedTuple, cast

from matplotlib import patches as mpatches
from matplotlib import path as mpath
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from Clue import ClueValueGenerator, Clue, ClueList, ClueValue
from GenericSolver import SolverByClue, Intersection


class Direction(Enum):
    Right = ((2, 0), 0, '→')
    RightDown = ((1, 1), 2, '↘')
    LeftDown = ((-1, 1), 1, '↙')
    Left = ((-2, 0), 0, '←')
    LeftUp = ((-1, -1), 2, '↖')
    RightUp = ((1, -1), 1, '↗')

    def delta(self, step: int = 1) -> Tuple[int, int]:
        (dx, dy), _, _ = self.value
        return step * dx, step * dy

    def same_type(self, other: 'Direction') -> bool:
        _, x, _ = self.value
        _, y, _ = other.value
        return x == y

    def __repr__(self) -> str:
        _, _, name = self.value
        return name


class Pentagon(NamedTuple):
    values: Sequence[int]
    directions: Sequence[Direction]

    def get_end_points(self) -> List[Tuple[int, int]]:
        x, y = 0, 0
        points = []
        for value, direction in zip(self.values, self.directions):
            dx, dy = direction.delta(value)
            x += dx
            y += dy
            points.append((x, y))
        assert (x, y) == (0, 0)
        return points

    def get_all_points(self) -> List[Tuple[int, int]]:
        x, y = 0, 0
        points = []
        for value, direction in zip(self.values, self.directions):
            dx, dy = direction.delta()
            for _ in range(value):
                x += dx
                y += dy
                points.append((x, y))
        assert (x, y) == (0, 0)
        return points

    def check_no_intersection(self) -> bool:
        points = self.get_all_points()
        return len(set(points)) == sum(self.values)

    def get_size(self) -> int:
        points = self.get_end_points()
        total = 0
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            total += x1 * y2 - x2 * y1
        if total < 0:
            total = -total
        assert total % 2 == 0
        return total // 2


ClueMap = Dict[int, List[Pentagon]]


def generate_map() -> ClueMap:
    result: Dict[int, List[Pentagon]] = collections.defaultdict(list)
    next_dir = {d1: [d2 for d2 in Direction if not d1.same_type(d2)] for d1 in Direction}
    for v1, v2, v3, v4, v5 in itertools.permutations(range(1, 10), 5):
        if v1 != min(v1, v2, v3, v4, v5) or v2 > v5:
            continue
        d1 = Direction.Right
        x1, y1 = d1.delta(v1)
        for d2 in (Direction.RightDown, Direction.LeftDown):
            x2, y2 = d2.delta(v2)
            for d3 in next_dir[d2]:
                x3, y3 = d3.delta(v3)
                for d4 in next_dir[d3]:
                    x4, y4 = d4.delta(v4)
                    for d5 in next_dir[d4]:
                        if d1 not in next_dir[d5]:
                            continue
                        x5, y5 = d5.delta(v5)
                        if x1 + x2 + x3 + x4 + x5 == 0 and y1 + y2 + y3 + y4 + y5 == 0:
                            pentagon = Pentagon((v1, v2, v3, v4, v5), (d1, d2, d3, d4, d5))
                            if pentagon.check_no_intersection():
                                size = pentagon.get_size()
                                result[size].append(pentagon)
    return result


def draw_pentagon(pentagon: Pentagon, label: Optional[str] = None, show: bool = True) -> None:
    points = [(0, 0)] + pentagon.get_end_points()

    min_x = min(x for x, _ in points)
    max_x = max(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)

    plt.figure(figsize=(7, 11))
    axis = plt.gca()
    plt.axis([min_x - 1, max_x + 1, max_y + 1, min_y - 1])
    axis.set_aspect(1.7)
    plt.axis('off')
    # plt.figure(figsize=(max_column * .8, max_row * .8), dpi=100)
    # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.

    path = mpath.Path(points, closed=True)
    patch = mpatches.PathPatch(path, facecolor='white', linewidth=3)
    axis.add_patch(patch)

    test_points = [(x, y + .5) for y in range(min_y - 2, max_y + 2)
                   for x in range(min_x - 1, max_x + 2)]
    test_results = path.contains_points(test_points)
    triangle_points = [(x, math.floor(y)) for ((x, y), result) in zip(test_points, test_results) if result]
    for i, (x, y) in enumerate(triangle_points):
        axis.text(x, y + .5, str(i + 1), fontsize=8, fontweight='bold',
                  verticalalignment='center', horizontalalignment='center')
        if (x + y) % 2 == 1:
            plt.plot([x - 1, x + 1, x, x - 1], [y, y, y + 1, y],
                     linewidth=0.5, color='black')
        else:
            plt.plot([x - 1, x + 1, x, x - 1], [y + 1, y + 1, y, y + 1],
                     linewidth=0.5, color='black')

    label = label or ''.join(map(str, pentagon.values))
    axis.text((min_x + max_x) / 2, max_y + 2, label, color='black',
              verticalalignment='top', horizontalalignment='center', size='30')

    all_points = pentagon.get_all_points()
    x_points, y_points = list(zip(*all_points))
    plt.plot(x_points, y_points, "bo")

    for (x1, y1), (x2, y2), length in zip(points, points[1:], pentagon.values):
        mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
        slope = (y2 - y1) / (x2 - x1)
        offset_x, offset_y = 0.5 * slope, -0.5
        if not path.contains_point((mid_x + offset_x, mid_y + offset_y)):
            axis.text(mid_x + offset_x, mid_y + offset_y, str(length), color='red', size='large',
                      verticalalignment='top', horizontalalignment='center')
        else:
            axis.text(mid_x - offset_x, mid_y - offset_y, str(length), color='red', size='large',
                      verticalalignment='top', horizontalalignment='center')
    if show:
        plt.show()


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
        clues.append(Clue(letter.upper(), True, location, 5, expression=str(value), generator=generator(value)))
    for (letter, value), location in zip(DOWNS, itertools.product((1, 5), (1, 3, 5, 7, 9))):
        clues.append(Clue(letter, False, location, 5, expression=str(value), generator=generator(value)))
    clue_list = ClueList(clues)
    return clue_list


class MySolver(SolverByClue):
    clue_map: ClueMap

    def __init__(self, clue_list: ClueList, clue_map: ClueMap):
        super(MySolver, self).__init__(clue_list)
        self.clue_map = clue_map

    def maybe_make_intersection(self, clue1: Clue, clue2: Clue) -> Optional[Intersection]:
        intersection = super().maybe_make_intersection(clue1, clue2)
        if intersection:
            return intersection
        if clue1.is_across == clue2.is_across:
            (x1, y1) = clue1.base_location
            (x2, y2) = clue2.base_location
            if clue1.is_across:
                if x1 == x2 and y1 != y2:
                    return Intersection(5 - y1, clue2, 5 - y2)
            else:
                if y1 == y2 and x1 != x2:
                    return Intersection(5 - x1, clue2, 5 - x2)
        return None

    def check_and_show_solution(self, known_clues: Dict[Clue, ClueValue]) -> None:
        super().check_and_show_solution(known_clues)
        with PdfPages('/tmp/foobar.pdf') as pdf:
            for clue in self.clue_list:
                triangles = int(clue.eval({}))
                answer = known_clues[clue]
                canonical_answer = min(answer[i:] + answer[:i] for i in range(5))
                if canonical_answer[1] > canonical_answer[-1]:
                    canonical_answer = canonical_answer[0] + canonical_answer[1:][::-1]
                canonical_lengths = tuple(map(int, list(canonical_answer)))
                pentagon = next(p for p in self.clue_map[triangles] if p.values == canonical_lengths)
                draw_pentagon(pentagon, answer, show=False)
                pdf.savefig()
                plt.close()


def get_dumped_map() -> ClueMap:
    with open("/tmp/magpie199.dmp", "rb") as file:
        return cast(ClueMap, pickle.load(file))


def test(key: int = 16, clue_map: Optional[ClueMap] = None) -> None:
    clue_map = clue_map or get_dumped_map()
    print(len(clue_map[key]))
    for pentagon in clue_map[key]:
        draw_pentagon(pentagon)


def run(clue_map: Optional[ClueMap] = None) -> None:
    clue_map = clue_map or get_dumped_map()
    clue_list = make_clue_list(clue_map)
    clue_list.verify_is_four_fold_symmetric()
    solver = MySolver(clue_list, clue_map)
    solver.solve(debug=False)


def build(dump: bool = False) -> None:
    value_map = generate_map()
    print(sum(len(value) for value in value_map.values()))
    keys = sorted(value_map.keys())
    print(keys[0], keys[-1])
    if dump:
        with open("/tmp/magpie199.dmp", "wb") as file:
            pickle.dump(value_map, file)
    else:
        assert value_map == get_dumped_map()


if __name__ == '__main__':
    run()
