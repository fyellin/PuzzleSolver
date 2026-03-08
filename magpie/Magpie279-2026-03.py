import re
from collections import defaultdict
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from itertools import chain, combinations, pairwise, product

from more_itertools import is_prime

from solver import (
    Clue,
    Clues,
    ClueValue,
    ConstraintSolver,
    DancingLinks,
    DLConstraint,
    Intersection,
    Orderer,
    generators,
)
from solver.dancing_links import get_row_column_optional_constraints
from solver.helpers import is_square

ACROSS_LENGTHS = "33/222/33/222/33"
DOWN_LENGTHS = "23/32/23/32/23/32"

CLUES = """
1 D + K = k
2 E + B = d
3 ? + H = J
4 ? + e = E
5 ? + m = E
6 e + ? = a
7 H + E = ?
8 C + a = ?
9 J + ? = b
10 e + ? = b
11 j + ? = g
12 ? + g = A
13 c + ? = g
14 h + b = ?
15 G + ? = f
16 j + L = ?
17 D + B = ?
18 A + i = ?
"""


@dataclass(frozen=True)
class Equation:
    index: int
    letters: str


class Magpie278(ConstraintSolver):
    @classmethod
    def run(cls, use_dancing_links: bool = False,
            print_result: bool = False,
            debug: bool = False
            ) -> None:
        solver = cls(print_result=print_result)
        if use_dancing_links:
            solver.solve_with_dancing_links()
        else:
            solver.solve(debug=debug, max_debug_depth=0)

    def __init__(self, *, print_result) -> None:
        clues = Clues.clues_from_clue_sizes(
            ACROSS_LENGTHS, DOWN_LENGTHS,
            across_names="ABCDEFGHJKLM", down_names="abcdefghijkm") # noqa
        self.print_result = print_result
        self.equations = self.get_constraints()
        self.letters = {clue.name for clue in clues}
        super().__init__(clues)

    def get_constraints(self) -> Sequence[Equation]:
        result = []
        for line in CLUES.strip().splitlines():
            match = re.fullmatch(r'(\d+) (.) \+ (.) = (.)\s*', line)
            index = int(match.group(1))
            letters = ''.join(match.group(2, 3, 4))
            result.append(Equation(index, letters))
        return result

    def get_initial_letter_values(self, *, prime: bool = False, square: bool = False
                                  ) -> dict[str, set[int]]:
        assert prime + square == 1
        if prime:
            generator, tester = generators.prime, is_prime
        else:
            generator, tester = generators.square, is_square
        letter_values = {}
        for letter in self.letters:
            clue = self.clue_named(letter)
            values = {*generator(clue)}
            pattern_generator = Intersection.make_pattern_generator(clue, (), self)
            pattern = pattern_generator({})
            letter_values[letter] = {x for x in values if pattern.fullmatch(str(x))}
        letter_values['?'] = {x for x in range(2000) if tester(x)}
        return letter_values

    def get_valid_triples(self, equation: Equation, values: list[set[int]]
                          ) -> list[tuple[int, int, int]]:
        data = [(v1, v2, t)
                for v1, v2 in product(values[0], values[1])
                if (t := (v1 + v2)) in values[2]]
        # Look to see if we have any intersections.
        for (ix1, l1), (ix2, l2) in combinations(enumerate(equation.letters), 2):
            if l1 == '?' or l2 == '?':
                continue
            clue1, clue2 = self.clue_named(l1), self.clue_named(l2)
            for intersection in Intersection.get_intersections(clue1, clue2):
                data = [triple for triple in data
                        if str(triple[ix1])[intersection.this_index] == str(triple[ix2])[
                            intersection.other_index]]
        return data

    #  A L c j i // g
    #  B C D E H K a b h// J d e k m
    #  F
    #  G // f
    #  M

    def solve_with_dancing_links(self):
        constraints: dict[Hashable, list[DLConstraint]] = {}
        optional_constraints = get_row_column_optional_constraints(6, 7)
        saved_constraints = defaultdict(list)
        prime_lv = self.get_initial_letter_values(prime=True)
        square_lv = self.get_initial_letter_values(square=True)
        ordering1 = (prime_lv, prime_lv, square_lv)
        ordering2 = (square_lv, square_lv, prime_lv)
        for equation in self.equations:
            letters = equation.letters
            values1 = [values[letter] for values, letter in zip(ordering1, letters)]
            values2 = [values[letter] for values, letter in zip(ordering2, letters)]
            triples = chain(self.get_valid_triples(equation, values1),
                            self.get_valid_triples(equation, values2))
            for triple in triples:
                constraint: list[DLConstraint] = [f'Equation-{equation.index}']
                row_info = {}
                for i, (letter, value) in enumerate(zip(letters, triple)):
                    optional_constraints.add(value_constraint := f'Value-{value}')
                    if letter != '?':
                        clue = self.clue_named(letter)
                        row_info |= dict(clue.dancing_links_rc_constraints(value))
                        # This value can only be used with this clue
                        constraint.append((value_constraint, f'Clue-{letter}'))
                    else:
                        # This value can not ever be used again.
                        constraint.append(value_constraint)
                name = equation, ''.join(equation.letters), *triple
                constraints[name] = [*constraint, *row_info.items()]
                saved_constraints[equation].append(name)
        self._handle_increasing_question_mark(
            constraints, optional_constraints, saved_constraints)
        for letter in 'FM':
            clue = self.clue_named(letter)
            for value in chain(square_lv[letter], prime_lv[letter]):
                optional_constraints.add(value_constraint := f'Value-{value}')
                constraints[100, letter, value] = [
                    f'Clue-{letter}',  # We must have a way of forcing one of these
                    (value_constraint, f'Clue-{letter}'),
                    *clue.dancing_links_rc_constraints(value)
                ]
        solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                              row_printer=self.row_printer)
        solver.solve(debug=10)

    def _handle_increasing_question_mark(
            self,
            constraints: dict[Hashable, list[DLConstraint]],
            optional_constraints: set[str],
            saved_constraints: defaultdict[Equation, list[tuple[int | str, ...]]]):
        for eqn1, eqn2 in pairwise(self.equations[2:]):
            u1, u2 = eqn1.letters.find('?'), eqn2.letters.find('?')
            names1, names2 = saved_constraints[eqn1], saved_constraints[eqn2]
            # The rows are (clue-number, letters values, values, ....)
            values = {*(name[u1 + 2] for name in names1),
                      *(name[u2 + 2] for name in names2)}
            orderer = Orderer.LT(f'{eqn1.index}-{eqn2.index}', values)
            optional_constraints.update(orderer.all_codes())
            for name in names1:
                constraints[name].extend(orderer.left(name[u1 + 2]))
            for name in names2:
                constraints[name].extend(orderer.right(name[u2 + 2]))

    def row_printer(self, result) -> None:
        values_dict = {}
        for (equation_number, letters, *values) in result:
            for letter, value in zip(letters, values, strict=True):
                if letter in "?":
                    continue
                clue = self.clue_named(letter)
                if clue in values_dict:
                    assert values_dict[clue] == str(value)
                else:
                    values_dict[clue] = str(value)
        if self.print_result:
            self.plot_board(values_dict)


if __name__ == '__main__':
    # Magpie278.run(use_dancing_links=False, print_result=False)
    Magpie278.run(use_dancing_links=True, print_result=True)
