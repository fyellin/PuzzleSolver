from itertools import combinations, pairwise, chain
import math
from collections import Counter, defaultdict
from functools import cache

from misc.primes import PRIMES
from solver import ClueValue, Clues, DancingLinks, EquationSolver


def DS(number: int | str) -> int:
    return sum(int(x) for x in str(number))


def DP(number: int | str) -> int:
    return math.prod(int(x) for x in str(number))


class Magpie267 (EquationSolver):
    CUBES = {i * i * i for i in range(100)}
    SQUARES = {i * i for i in range(100)}
    TRIANGLES = {i * (i + 1) // 2 for i in range(100)}
    OK_DPS = (1, 2, 2, 4, 4, 5, 9, 12, 18, 40, 40, 45, 54, 56, 63, 160, 432)
    SOLUTION = {'3a': 15, '4d': 58, '12d': 78, '11a': 917, '11d': 91, '14a': 11,
                '15a': 854, '7a': 518, '2d': 95, '10d': 114, '13a': 21, '8d': 192,
                '5a': 22, '6d': 261, '1d': 121, '1a': 169, '9a': 689}

    @classmethod
    def run(cls):
        solver = cls()
        solver.solve()

    def __init__(self) -> None:
        self.ok_dp_counter = Counter(self.OK_DPS)
        self.pairwise = list(pairwise(self.OK_DPS))
        self.triplewise = [(a, b, c) for (a, b), (_, c) in
                           pairwise(self.pairwise)]
        clues = Clues.clues_from_clue_sizes("32/23/131/32/23", "32/131/212/131/23")
        super().__init__(clues)

    def solve(self):
        constraints = {}
        optional_constraints = set(f'r{r}c{c}' for r in range(1, 6) for c in range(1, 6))
        by_number_and_alt = defaultdict(list)
        by_number_and_location = defaultdict(list)
        all_numbers = [value for value in range(10, 1000) if DP(value) in self.OK_DPS]
        all_squares = [x for x in all_numbers if x in self.SQUARES]

        # if not self.foo(all_numbers):
        #     return;

        for number in all_numbers:
            dp = DP(number)
            if number < 100 and number in all_squares:
                # eliminate two digit squares
                continue
            optional_constraints.add(f'#{number}')
            alternatives = self.ok_dp_counter[dp]
            assert 1 <= alternatives <= 2
            for clue in self._clue_list:
                for alt in range(alternatives):
                    if clue.length == len(str(number)):
                        optional_constraints.add(temp := f'{clue.name}-{number}')
                        constraint = [clue.name, f"DP-{dp}-{alt}", f"#{number}", temp]
                        constraint.extend((f'r{r}c{c}', letter)
                                          for (r, c), letter in zip(clue.locations, str(number)))
                        constraints[(clue.name, number, dp, alt)] = constraint
                        by_number_and_alt[number, alt].append(constraint)
                        by_number_and_location[number, clue].append(constraint)

        # Just so we don't have duplicates.  Make sure alt=0 goes with the smaller
        # number and alt=1 goes with the higher number
        for dp in (key for key, value in self.ok_dp_counter.items() if value == 2):
            numbers = [number for number in all_numbers if DP(number) == dp]
            for number1, number2 in combinations(numbers, 2):
                assert number1 < number2
                constraint = f'DP:{number1}<{number2}'
                optional_constraints.add(constraint)
                for c in chain(by_number_and_alt[number1, 1],
                               by_number_and_alt[number2, 0]):
                    c.append(constraint)

        # We must have two three-digit squares in the grid.  We make all three digit
        # squares be required, but allow all combinations of the others as extra.
        large_squares = [x for x in all_squares if x >= 100]
        optional_constraints -= {f"#{number}" for number in large_squares}
        for a, b in combinations(large_squares, 2):
            constraints['EXTRA', "SQUARES", a, b] = [
                'SQUARESx2',
                *(f'#{number}' for number in large_squares if number not in (a, b))
            ]

        # Make sure that the two squares that *do* end up in the grid intersect.
        three_clues = [clue for clue in self._clue_list if clue.length == 3]
        for (clue1, clue2) in combinations(three_clues, 2):
            if not clue1.location_set.isdisjoint(clue2.location_set):
                continue
            item = f"square-{clue1.name}-{clue2.name}"
            optional_constraints.add(item)
            for number in large_squares:
                for constraint in by_number_and_location[number, clue1]:
                    constraint.append(item)
                for constraint in by_number_and_location[number, clue2]:
                    constraint.append(item)

        self.constraints_for_two_digits(all_numbers, constraints)

        def row_printer(result):
            solution = {clue: int(value)
                        for row in result for clue, value, *_ in [row]
                        if clue != 'EXTRA'}
            if self.verify_solution(solution):
                print('***', solution)
                clue_values = {self.clue_named(name): ClueValue(str(value))
                               for name, value in self.SOLUTION.items()}
                self.plot_board(clue_values, subtext=1.2)

        solver = DancingLinks(constraints,
                              optional_constraints=optional_constraints,
                              row_printer=row_printer)
        solver.solve(debug=0)

    def constraints_for_two_digits(self, all_numbers, constraints):
        small = [value for value in all_numbers
                 if value < 100 and value not in self.SQUARES]
        # We know that there are four small triangles that aren't square.
        a, b, c, d = [value for value in small if value in self.TRIANGLES]
        x1 = [x for x in small if x not in (a, b, c, d)]
        possibilities = []
        for e, f in combinations(x1, 2):
            if f % e != 0:
                continue
            x2 = [x for x in x1 if x not in (e, f) and x not in PRIMES]
            for g, h in combinations(x2, 2):
                if tuple(sorted((DP(g), DP(h)))) not in self.pairwise:
                    continue
                values = (a, b, c, d, e, f, g, h)
                if Counter(DP(x) for x in values) <= self.ok_dp_counter:
                    cube_sums = [var for var in combinations(values, 4)
                                 if sum(var) in self.CUBES]
                    if cube_sums:
                        possibilities.append((values, cube_sums))

        summed_small_clues = ['2d', '5a', '13a', '12d']  # must contain the sums
        unsummed_small_clues = [clue.name for clue in self._clue_list
                                if clue.length == 2 and clue.name not in summed_small_clues]
        for values, cube_sums in possibilities:
            unused = [x for x in small if x not in values]
            for cube_sum in cube_sums:
                constraint = ['TWO-DIGITS']
                constraint.extend(f'#{number}' for number in unused)
                constraint.extend(f'{name}-{number}'
                                  for number in values if number not in cube_sum
                                  for name in summed_small_clues)
                constraint.extend(f'{name}-{number}'
                                  for number in cube_sum
                                  for name in unsummed_small_clues)
                constraints['EXTRA', '2-letter', values, cube_sum] = constraint

    def verify_solution(self, solution):
        return self.check_two_digits(solution) and self.check_three_digits(solution)

    def check_two_digits(self, solution):
        return True

    def check_three_digits(self, solution):
        three_digits = set(x for x in solution.values() if x >= 100)
        assert sum(x in self.SQUARES for x in three_digits) == 2
        clue1, clue2 = [self.clue_named(name) for name, value in solution.items() if
                        value in self.SQUARES]
        assert clue1.location_set & clue2.location_set

        x1 = three_digits - {solution[clue1.name], solution[clue2.name]}
        ds_set = [x for x in x1 if x % DS(x) == 0]
        for (a, b, c, d) in combinations(ds_set, 4):
            if set(str(a)) & set(str(b)) & set(str(c)) & set(str(d)):
                e, f, g = list(x1 - {a, b, c, d})
                if e not in PRIMES and f not in PRIMES and g not in PRIMES:
                    if DS(e) in PRIMES and DS(f) in PRIMES and DS(g) in PRIMES:
                        if tuple(sorted([DP(e), DP(f), DP(g)])) in self.triplewise:
                            return True
        return False

    def solve3(self):
        clues = {self.clue_named(name): ClueValue(str(value))
                 for name, value in self.SOLUTION.items()}
        locations = {location: int(letter) for clue, value in clues.items()
                     for location, letter in zip(clue.locations, value)}
        string = tuple(locations[r, c] for r in range(1, 6) for c in range(1, 6))

        @cache
        def recurse(stuff, index):
            alphabet = " ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            if index == 25:
                print(stuff)
                return
            recurse(stuff + alphabet[string[index]], index + 1)
            if index <= 23 and (o := string[index] * 10 + string[index + 1]) <= 26:
                recurse(stuff + alphabet[o], index + 2)

        # recurse("", 0)
        self.plot_board(clues, subtext=1.2)


if __name__ == '__main__':
    Magpie267.run()
