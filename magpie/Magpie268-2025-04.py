import math
from functools import cache

from solver import Clues, DancingLinks, Encoder
from solver.equation_solver import EquationSolver


@cache
def DS(number: int | str) -> int:
    return sum(int(x) for x in str(number))

@cache
def DP(number: int | str) -> int:
    return math.prod(int(x) for x in str(number))


def possibilities(digits, is_across):
    if is_across:
        subf, addf = DS, DP
    else:
        subf, addf = DP, DS
    v1, v2 = 10 ** (digits - 1), 10 ** digits
    result = []
    for value in range(v1, v2):
        for low in range(v1, value):
            if '0' in str(low): continue
            high = value + addf(low)
            if high < v2 and low == value - subf(high) and '0' not in str(high):
                result.append((low, high, value))
    return result

class Magpie268 (EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.verify_is_180_symmetric()
        solver.solve()

    def __init__(self) -> None:
        clues = Clues.clues_from_clue_sizes("22/31/13/22", "22/13/31/22")
        super().__init__(clues)

    def solve(self):
        encoder = Encoder.digits()
        constraints = {}
        optional = set()
        across_pairs = ((1, 10), (2, 9), (4, 7))
        down_pairs = ((1, 8), (2, 5), (3, 6))

        for is_across in (True, False):
            if is_across:
                tag, pairs = 'a', across_pairs
            else:
                tag, pairs = 'd', down_pairs
            for pair in pairs:
                clue1, clue2 = clues = tuple([self.clue_named(f'{num}{tag}') for num in pair])
                assert clue1.length == clue2.length
                triples = possibilities(clues[0].length, is_across)
                if is_across and clue1.length == 3:
                    triples = [triple for triple in triples if triple[2] == 496]
                for (low, high, start) in triples:
                    # We don't know which clue gets the low value and which gets the high
                    for values in ((low, high), (high, low)):
                        # Include low, high, value since they are supposed to be unique
                        constraint = [clue1.name, clue2.name, str(low), str(high), str(value)]
                        optional.update(constraint[2:])
                        # Add to the constrant that clue1 = value1 and clue2 = value2
                        for clue, value in zip(clues, values):
                            for location, letter in zip(clue.locations, str(value)):
                                if self.is_intersection(location):
                                    encodes = encoder.encode(letter, location, is_across)
                                    constraint.extend(encodes)
                        if str(start) == str(start)[::-1]:
                            # There is precisely one "start" value that's a palindrome.
                            constraint.append('palindrome')
                        constraints[clues, values] = constraint

        def row_printer(result):
            solution = [(clue, str(value)) for (clues, values) in result for clue, value in zip(clues, values)]
            print(solution)
            self.plot_board(dict(solution))

        solver = DancingLinks(constraints, optional_constraints=optional, row_printer=row_printer)
        solver.solve(debug=100)


if __name__ == '__main__':
    Magpie268.run()
