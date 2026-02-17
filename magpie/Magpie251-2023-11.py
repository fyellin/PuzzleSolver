import itertools
from functools import cache

from sortedcontainers import SortedDict

from misc.primes import PRIMES
from solver import Clue, ConstraintSolver, DancingLinks, generators

C = [x for i in range(2, 100) for x in [i ** 3] if 2 <= x < 10_000]
S = [x for i in range(2, 1000) for x in [i ** 2] if 2 <= x < 10_000]
T = [x for i in range(2, 1000) for x in [i * (i + 1) // 2] if 2 <= x < 10_000]
P = [x for x in PRIMES if 2 <= x < 10_000]
P_set = set(P)
F = [2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765]


def okay(x):
    return len(set(str(x))) <= 2 or '0' in str(x)


def okay2(x):
    return len(set(str(x))) <= 2 and '0' not in str(x)


def run():
    global result
    result = []
    run1(SortedDict())
    for x in result:
        print(x)
    print(len(result))


def run1(v):
    for a1 in P:
        if 10 <= a1 <= 99:
            run2(v | {1: a1})


def run2(v):
    for t in T:
        a2 = 2 * t
        if v[1] < a2 < 100:
            run3(v | {2: a2})


def run3(v):
    for a3 in P:
        if v[2] < a3 < 100:
            run4(v | {3: a3})


def run4(v):
    for t in T:
        a4 = v[1] * t
        if v[3] < a4 < 100:
            run5(v | {4: a4})


def run5(v):
    for a5 in F:
        if v[4] < a5 < 100:
            run6(v | {5: a5})


def run6(v):
    for a6 in range(v[5], 100):
        if a6 % 8 == 0 or a6 % 27 == 0:
            run7(v | {6: a6})


def run7(v):
    for a7 in F:
        if v[6] < a7 < 100 and a7 in T:
            run8(v | {7: a7})


def run8(v):
    a8 = v[1] + v[6]
    a9 = v[1] + a8
    a10 = v[3] + v[6]
    if v[7] < a8 < a9 < a10 < 100:
        run11(v | {8: a8, 9: a9, 10: a10})


def run11(v):
    for a11 in (16, 81):
        a12 = v[4] + v[6]
        if v[10] < a11 < a12 < 100:
            run11a(v | {11: a11, 12: a12})


def run11a(v):
    for a19 in (x for x in F if 100 <= x <= 999 and okay(x)):
        a44 = v[4] * a19 - v[3]
        if 1000 <= a44 <= 9999 and okay(a44):
            for a45 in (x ** 5 for x in range(2, 10)
                        if a44 < x ** 5 <= 9999 and okay(x ** 5)):
                run12(v | {19: a19, 44: a44, 45: a45})


def run12(v1):
    # 1-12, 19, 44, 45
    # 13, 14, 15, 17, 20, 23, 24, 26, 29, 30, 33, 38
    for v2 in handle_T():
        v = v1 | v2
        if all(x < y for x, y in itertools.pairwise(v)):
            if sum('0' in str(x) for x in v.values()) <= 2:
                assert sum('0' in str(x) for x in v.values()) == 2
                run16(v)


def run16(v):
    # 1-15, 17, 19-20, 23, 24, 26, 29-30, 33, 38, 44, 45
    for s in S:
        if v[15] < (a16 := s + 1) < v[17] and okay2(a16):
            run18(v | {16: a16})


def run18(v):
    # 1-17, 19-20, 23, 24, 26, 29-30, 33, 38, 44, 45
    for a18 in P:
        if v[17] < a18 < v[19] and okay2(a18):
            run21(v | {18: a18})


def run21(v):
    # 1-20, 23, 24, 26, 29-30, 33, 38, 44, 45
    a21 = v[20] + 1
    a22 = v[1] + v[20]
    if v[20] < a21 < a22 < v[23] and okay2(a21) and okay2(a22):
        run25(v | {21: a21, 22: a22})


def run25(v):
    # 1-24, 26, 29-30, 33, 38, 44, 45
    for a25 in range(v[24] + 1, v[26]):
        if not okay2(a25):
            continue
        a28 = a25 + v[14]
        a32 = a28 + v[14]
        if okay2(a28) and okay2(a32) and v[26] < a28 < v[29] < v[30] < a32 < v[33]:
            run27(v | {25: a25, 28: a28, 32: a32})


def run27(v):
    # 1-26, 28-30, 32-33, 38, 44, 45
    for a27 in range(v[26] + 1, v[28]):
        a31 = a27 + v[14]
        a35 = a31 + v[14]
        if okay2(a27) and okay2(a31) and okay2(a35):
            if a35 == v[17] + a27 and a35 in P_set:
                if v[30] < a31 < v[32] < v[33] < a35 < v[38]:
                    run34(v | {27: a27, 31: a31, 35: a35})


def run34(v):
    # 1-33, 35, 38, 44, 45
    a34 = v[5] + v[33]
    a36 = v[13] + v[32]
    a37 = v[9] + a34
    a39 = v[11] + v[21] + v[30]
    if okay2(a34) and okay2(a36) and okay2(a37) and okay2(a39):
        if a34 in P_set and a36 in P_set and a37 in P_set:
            if v[33] < a34 < v[35] < a36 < a37 < v[38] < 1000 <= a39 < v[44]:
                run40(v | {34: a34, 36: a36, 37: a37, 39: a39})


def run40(v):
    assert all(x < y for x, y in itertools.pairwise(v))
    # 1-39, 44, 45
    for a40 in (3 * t for t in T if okay2(3 * t) and v[39] < 3 * t < v[45]):
        # a41 = 2 * (v[7] + a40)
        a42 = v[1] * v[21] + v[36]
        a41 = 2 * v[7] + a40
        a43 = v[15] + v[33] + a42
        a46 = v[12] * v[14] - v[32]
        if okay2(a41) and okay2(a42) and okay2(a43) and okay2(a46):
            if v[39] < a40 < a41 < a42 < a43 < v[44] < v[45] < a46 <= 9999:
                done(v | {40: a40, 41: a41, 42: a42, 43: a43, 46: a46, })


def done(v):
    global result
    if v[6] == 48:
        result.append(list(v.values()))

@cache
def handle_t2():
    for a14 in range(100, 143):
        if not okay(a14):
            continue
        items = [x for x in range(a14, 1000, a14) if okay(x)]
        if len(items) < 7 or sum('0' not in str(x) for x in items) < 5:
            continue
        for a17, a20, a23, a26, a29, a33, a38 in itertools.combinations(items[1:], 7):
            if a29 not in T: continue
            print(a14, a17, a20, a23, a26, a29, a33, a38)


@cache
def handle_T():
    results = []
    t1 = [x for x in T if 100 <= x <= 999 and okay(x)]
    t4 = [x for t in T for x in [4 * t] if 100 <= x <= 999 and okay(x)]

    for a13, a29, a30 in itertools.combinations(t1, 3):
        for a15, a24 in itertools.combinations(t4, 2):
            if a13 < a15 < a24 < a29 < a30 <= 999:
                for a14 in range(a13 + 1, a15):
                    if a29 % a14 == 0:
                        combos1 = [x for x in range(a15 + 1, a24)
                                   if x % a14 == 0 if okay(x)]
                        combos2 = [x for x in range(a24 + 1, a29)
                                   if x % a14 == 0 if okay(x)]
                        combos3 = [x for x in range(a30 + 1, 1000)
                                   if x % a14 == 0 if okay(x)]
                        for a17, a20, a23 in itertools.combinations(combos1, 3):
                            for a26 in combos2:
                                for a33, a38 in itertools.combinations(combos3, 2):
                                    result = {13: a13, 14: a14, 15: a15, 17: a17, 20: a20,
                                              23: a23, 24: a24, 26: a26, 29: a29, 30: a30,
                                              33: a33, 38: a38}
                                    zeros = sum('0' in str(x) for x in result.values())
                                    if zeros > 2:
                                        continue
                                    assert zeros == 2
                                    results.append(result)
    return results


ACROSS = (2133, 13311, 4212, 1134, 333, 4311, 2124, 11331, 3312)
DOWNS = (3312, 11331, 2124, 4311, 333, 1134, 4212, 13311, 2133)

NUMBERS = [
    [11, 12, 23, 33, 34, 54, 55, 65, 76, 77, 81, 87, 105, 111, 112, 122, 222, 223, 233, 333, 334, 344, 444, 544, 554, 555, 655, 665, 666, 703, 766, 776, 777, 811, 877, 881, 887, 888, 1118, 2223, 2333, 4555, 5444, 7666, 7776, 8881],
    [11, 12, 23, 33, 34, 54, 55, 65, 76, 77, 81, 87, 105, 111, 112, 122, 222, 227, 233, 333, 334, 344, 444, 544, 554, 555, 655, 665, 666, 703, 766, 776, 777, 811, 877, 881, 887, 888, 1118, 2223, 2333, 4555, 5444, 7666, 7776, 8881],
    [11, 12, 23, 33, 34, 54, 55, 65, 76, 77, 81, 87, 105, 111, 112, 122, 222, 229, 233, 333, 334, 344, 444, 544, 554, 555, 655, 665, 666, 703, 766, 776, 777, 811, 877, 881, 887, 888, 1118, 2223, 2333, 4555, 5444, 7666, 7776, 8881],
    [11, 12, 23, 33, 34, 54, 55, 65, 76, 77, 81, 87, 105, 111, 112, 122, 222, 223, 233, 333, 334, 344, 444, 544, 554, 555, 655, 665, 666, 703, 766, 776, 777, 811, 877, 881, 887, 999, 1118, 2223, 2333, 4555, 5444, 7666, 7776, 8881],
    [11, 12, 23, 33, 34, 54, 55, 65, 76, 77, 81, 87, 105, 111, 112, 122, 222, 227, 233, 333, 334, 344, 444, 544, 554, 555, 655, 665, 666, 703, 766, 776, 777, 811, 877, 881, 887, 999, 1118, 2223, 2333, 4555, 5444, 7666, 7776, 8881],
    [11, 12, 23, 33, 34, 54, 55, 65, 76, 77, 81, 87, 105, 111, 112, 122, 222, 229, 233, 333, 334, 344, 444, 544, 554, 555, 655, 665, 666, 703, 766, 776, 777, 811, 877, 881, 887, 999, 1118, 2223, 2333, 4555, 5444, 7666, 7776, 8881],
]


class Solver251 (ConstraintSolver):
    @staticmethod
    def run(numbers):
        solver = Solver251(numbers)
        solver.verify_is_180_symmetric()
        if numbers:
            print(numbers)
            solver.dancing_links(numbers)
        else:
            solver.plot_board()

    def __init__(self, numbers):
        clues = self.get_clues(numbers)
        super().__init__(clues)

    def dancing_links(self, numbers):
        numbers = [str(x) for x in numbers]
        constraints = {}
        optional_constraints = {f'r{r}c{c}' for r in range(1, 10) for c in range(1, 10)}
        mapper = {'999': '888', '227': '223', '229': '223'}
        for clue in self._clue_list:
            for number in numbers:
                if clue.length == len(number):
                    constraint = [mapper.get(number, number), clue.name,
                                  *((f'r{r}c{c}', letter)
                                    for (r, c), letter in zip(clue.locations, number))]
                    constraints[f'{clue.name}-{number}'] = constraint
        solver = DancingLinks(constraints, optional_constraints=optional_constraints)
        solver.solve(debug=100)

    def get_clues(self, numbers):
        generator = generators.known(*numbers)
        clues = []
        for is_across, items in (True, ACROSS), (False, DOWNS):
            name = 'a' if is_across else 'd'
            for row, descriptor in enumerate(items, start=1):
                lengths = [int(i) for i in str(descriptor)]
                for column, length in zip(itertools.accumulate(lengths, initial=1), lengths):
                    if length != 1:
                        (x, y) = (row, column) if is_across else (column, row)
                        clue = Clue(f'{x}{y}{name}', is_across, (x, y), length,
                                    generator=generator)
                        clues.append(clue)

        return clues

    COLORS = ['#e6194B', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#42d4f4', '#f032e6',
              '#bfef45', '#fabed4', '#469990', '#dcbeff', '#9A6324', '#fffac8', '#800000', '#aaffc3',
              '#808000', '#ffd8b1', '#000075', '#a9a9a9', '#000000']

    def draw_grid(self, location_to_clue_numbers, location_to_entry, **args) -> None:
        # self.COLORS[1] = '#A0A0A0'
        # shading = {square : 'red' for square in squares}
        #shading = {square: self.COLORS[int(value) + 1] for square, value in location_to_entry.items()}
        self.location_to_entry = location_to_entry
        super().draw_grid(location_to_entry=location_to_entry,
                          location_to_clue_numbers={},
                          # shading=shading,
                          subtext="\n8 T + 1 = S",
                          # grid_drawer = self.grid_drawer,
                          extra = self.extra,
                          **args)


    def extra(self, plt, axes):
        la = self.location_to_entry
        for row in range(1, 10):
            for column in range(2, 10):
                if la[row, column - 1] != la[row, column]:
                    axes.plot([column, column], [row, row + 1], 'red', linewidth=15)
        for row in range(2, 10):
            for column in range(1, 10):
                if la[row - 1, column] != la[row, column]:
                    axes.plot([column, column + 1], [row, row], 'red', linewidth=15)


if __name__ == '__main__':
    # Solver251.run(tuple(sorted({x for numbers in NUMBERS for x in numbers})))  # 1654
    Solver251.run(NUMBERS[0])
