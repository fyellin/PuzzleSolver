import itertools
import re
from collections import defaultdict
from itertools import permutations

from misc.Pentomino import Pentomino, Tiling, intersection_printer
from misc.UnionFind import UnionFind
from solver import DancingLinks


def find_values():
    primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41}
    h, c = 2, 3
    primes -= {c, h}

    pattern3 = re.compile('[1-9]{3}')
    pattern4 = re.compile('[1-9]{4}')

    def okay_a345(value):
        if not pattern3.match(value):
            return False
        if '1' in value and not(value[0] == value[1] != '1'):
            return False
        if '5' in value and value != '551':
            return False
        if '6' in value and not (value[0] != '6' and value[1] == value[2] == '6'):
            return False
        return True

    def okay_a6(value):
        if not pattern4.match(value):
            return False
        if '1' in value or '6' in value:
            return False
        if '5' in value and not (value[0] != value[1] == value[2] != value[3]):
            return False
        return True

    def okay_d3456(value):
        if not pattern3.fullmatch(value):
            return False
        if '1' in value and not('1' == value[0] != value[1] == value[2]):
            return False
        if '5' in value and value != '555':
            return False
        if '6' in value and not('6' == value[0] == value[1] != value[2]):
            return False
        return True

    for a, d, g in permutations(primes, 3):
        if not okay_a6(a6 := str(a * c * d * g)):
            continue
        primes2 = primes - {a, d, g}
        for j, k, l in permutations(primes2, 3):
            if not okay_a345(a5 := str(j * k)):
                continue
            if not okay_d3456(d5 := str(k * l)):
                continue
            if not okay_d3456(d3 := str(g * k * l - c)):
                continue
            if not okay_d3456(d4 := str(g * k * l + c)):
                continue
            primes3 = primes2 - {j, k, l}
            for b, e, f, m, n in permutations(primes3):
                if not okay_a345(a3 := str(b * d)):
                    continue
                if not okay_a345(a4 := str(c * h * m)):
                    continue
                if not okay_d3456(d6 := str(m * (e * h - f))):
                    continue

                print((a3, a4, a5), a6, (d3, d4, d5, d6),
                      (a, b, c, d, e, f, g, h, j, k, l, m, n))


def get_main_tiling():
    results = Pentomino.get_all_pentominos(7)

    constraints = {}
    optional_constraints = set()
    for name, cell_list in results.items():
        name_info = f'Shape-{name}'
        for pentomino in cell_list:
            constraints[(name, pentomino)] = [
                name_info,
                *[f'r{x}c{y}' for x, y in pentomino]
            ]
        optional_constraints.add(name_info)

    for x, y in itertools.product((2, 6), repeat=2):
        constraints[('Given', (x, y))] = [f'r{x}c{y}', f'Given-r{x}c{y}']

    count = count2 = 0
    all_tilings = []

    def my_printer(solution):
        nonlocal count, count2
        tiling = convert_to_tiling(solution)
        count += 1

        maps = tiling.map
        a, b, c, d = (maps[(3, x)] for x in range(4, 8))
        if a == c and a != b and a != d and b != d:
            count2 += 1
            all_tilings.append(tiling)
            print(tiling)

    def convert_to_tiling(solution):
        mapping = {x: '-' for x in itertools.product((2, 6), repeat=2)}
        for name, info in solution:
            if name != 'Given':
                mapping.update((cell, name) for cell in info)
        return Tiling(mapping, 7)

    solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                          row_printer=my_printer)
    solver.solve(debug=0)
    print(count, count2)


SAFE_TILINGS = (
    Tiling("YFFTTTIY-FFT-IYYFUTUIYWWUUUIWWVPPPIW-VPP-LVVVLLLL", 7),
    Tiling("YTTTFFIY-TFF-IYYTUFUIYWWUUUIWWVPPPIW-VPP-LVVVLLLL", 7),
    Tiling("YFFTTTIY-FFT-IYYFUTUIYPPUUUIVPPPNNIV-NNN-LVVVLLLL", 7),
    Tiling("YTTTFFIY-TFF-IYYTUFUIYPPUUUIVPPPNNIV-NNN-LVVVLLLL", 7),
    Tiling("NNNTTTIZ-NNT-IZZZUTUIWWZUUUIVWWPPPIV-WPP-LVVVLLLL", 7),
    Tiling("VVVTTTIV-FFT-IVFFUTUIPPFUUUIPPYYYYIP-NNY-LNNNLLLL", 7),
    Tiling("YYYYFFIP-YFF-IPPTUFUIPPTUUUIVTTTNNIV-NNN-LVVVLLLL", 7),
    Tiling("YYYYFFIT-YFF-ITTTUFUITWWUUUIWWVPPPIW-VPP-LVVVLLLL", 7),
    Tiling("YYYYFFIT-YFF-ITTTUFUITPPUUUIVPPPNNIV-NNN-LVVVLLLL", 7),
    Tiling("YYYYFFIZ-YFF-IZZZUFUIWWZUUUIVWWPPPIV-WPP-LVVVLLLL", 7),
)

def update_safe_tilings():
    tilings = [x for x in SAFE_TILINGS
               if x.map[1, 4] == x.map[1, 5]
               if x.map[5, 4] != x.map[5, 6]
               ]
    for x in tilings:
        print(x)
        # row_printer(x)
    if len(tilings) == 1:
        tilings[0].show()
    else:
        show_forced_sharing(tilings)


def show_forced_sharing(safe_tilings=SAFE_TILINGS):
    uf = UnionFind()
    squares = list(safe_tilings[0].map.keys())
    for s1, s2 in itertools.combinations(squares, 2):
        if uf.find(s1) != uf.find(s2):
            if all(tiling.map[s1] == tiling.map[s2] for tiling in safe_tilings):
                uf.union(s1, s2)

    token_map = defaultdict(list)
    for square in squares:
        token_map[uf.find(square)].append(square)

    result = []
    for items in token_map.values():
        if len(items) > 1 and (2, 2) not in items:
            result.append(items)

    intersection_printer(result, 7)


def show_solution():
    mapping = dict(U=6, T=5, I=1, Y=7, F=9, L=3, P='8', N='2', V='4')
    tiling = Tiling("YFFTTTIY-FFT-IYYFUTUIYPPUUUIVPPPNNIV-NNN-LVVVLLLL", 7)
    tiling.show(mapping=mapping)
    tiling.show(mapping=mapping, white=True)


if __name__ == '__main__':
    show_solution()
