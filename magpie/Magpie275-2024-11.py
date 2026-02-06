from __future__ import annotations

import itertools
from collections.abc import Iterable, Sequence
from functools import cache
from typing import Any

from solver import Clue, ClueValue, EquationSolver, Evaluator, Letter, Location, \
    MultiEquationSolver
from solver.equation_solver import KnownClueDict, KnownLetterDict

ACROSS_LENGTHS = "413/332/44/44/233/314"
DOWN_LENGTHS = "222/33/24/33/33/42/33/222"

EQUATIONS = """
1 (H + A)(S−H) + ISH
2 O + H − (I − O(A + N))S
3 A + R + (TI−S−T)E
4 (((S + T)R−I)/A)(T + E)
5 T(S + (E + T/S)E)
6 T + O(E − T + O + E)
7 E + N + (T + R)E(A + T)
8 ((T + A)T + T)O + O−S
9 R(E + T + IR−E) + E
10 R(E(E−N)−T) + E−R
11 H + O−T(S−H−OT)
12 (AE −R + A)(T + O)−R
13 (HO −N)(I−T)−O−N
14 H(O−R−N)I−S-H
15 E(S + T(H + E))−T−E
16 (H + EA)(R + E + R)−S
"""


def wrapper(self, value_dict: dict[Letter, int]) -> Iterable[ClueValue]:
    try:
        result = self._compiled_code(*(value_dict[x] for x in self._vars))
        if (int_result := int(result)) == result:
            square_result = int_result * int_result
            if 100_000_000 <= square_result <= 999_999_999:
                value = str(square_result)
                if len(set(value)) == 8:
                    return wrapper_encode(value)
    except ArithmeticError:
        pass
    return ()

@cache
def wrapper_encode(value: str) -> Sequence[ClueValue]:
    value = list(value)
    seen = set()
    for index, letter in enumerate(value):
        if letter in seen:
            break
        seen.add(letter)
    else:
        assert False, "should not reach here"
    removed = {''.join(value[:i] + value[i + 1:]) for i, ch in enumerate(value) if ch == letter}

    result = []
    for eight in removed:
        for i in range(0, 8):
            temp = eight[i:] + eight[:i]
            result.append(letter + temp)
            result.append(letter + temp[::-1])
    return result

class Magpie275 (MultiEquationSolver):
    @classmethod
    def run(cls) -> None:
        solver = cls()
        solver.solve(debug=True, max_debug_depth=1)
        # solver.solve()

    def __init__(self) -> None:
        clues = self.get_clues()
        values = [i * i for i in range(1, 10)]
        super().__init__(clues, items=values)

    def get_clues(self):
        equations = []
        for counter, line in enumerate(EQUATIONS.strip().splitlines(), start=1):
            number, equation = line.split(' ', 1)
            assert counter == int(number)
            equations.append((counter, equation))
        centers = itertools.product(range(2, 9, 2), repeat=2)
        clues = []
        for (r, c), (counter, equation) in zip(centers, equations, strict=True):
            locations = ((r, c), (r - 1, c - 1), (r - 1, c), (r - 1, c + 1), (r, c + 1),
                         (r + 1, c + 1), (r + 1, c), (r + 1, c - 1), (r, c - 1))
            clue = Clue(str(counter), True, (r, c), 9, expression=equation, locations=locations)
            clue.evaluators = Evaluator.create_evaluators(equation, wrapper=wrapper)
            clues.append(clue)
        return clues

    def get_allowed_regexp(self, location: Location) -> str:
        return '.'

    def show_solution(self, known_clues: KnownClueDict,
                      known_letters: KnownLetterDict) -> None:
        for clue in self._clue_list:
            evaluator, = clue.evaluators
            result = evaluator.raw_call(known_letters)
            int_result = int(result)
            print(clue.name, int_result * int_result)
        super().show_solution(known_clues, known_letters)

    def draw_grid(self, left_bars, top_bars, location_to_clue_numbers, **args: Any) -> None:
        left_bars = [(r, c + delta) for r, c in location_to_clue_numbers for delta in (0, 1)]
        top_bars = [(r + delta, c) for r, c in location_to_clue_numbers for delta in (0, 1)]
        super().draw_grid(location_to_clue_numbers=location_to_clue_numbers,
                          left_bars=left_bars, top_bars=top_bars,
                          **args)

def is_okay(value):
    if (ivalue := int(value)) == value:
        square_value = ivalue * ivalue
        if 100_000_000 <= square_value <= 999_999_999:
            value = str(square_value)
            if len(set(value)) == 8:
                return True
    return False

def test1():
    """
<Clue 5> ('E', 'S', 'T')
<Clue 6> ('O',)
<Clue 11> ('H',)
<Clue 15> ()
<Clue 8> ('A',)
<Clue 12> ('R',)
<Clue 16> ()
<Clue 7> ('N',)
<Clue 10> ()
<Clue 9> ('I',)
<Clue 14> ()
<Clue 13> ()
<Clue 1> ()
<Clue 2> ()
<Clue 3> ()
<Clue 4> ()

1 (H + A) * (S - H) + I * S * H
2 O + H - (I - O * (A + N)) * S
3 A + R + (T * I - S - T) * E
4 ((S + T) * R - I) / A * (T + E)
5 T * (S + (E + T / S) * E)
6 T + O * (E - T + O + E)
7 E + N + (T + R) * E * (A + T)
8 ((T + A) * T + T) * O + O - S
9 R * (E + T + I * R - E) + E
10 R * (E * (E - N) - T) + E - R
11 H + O - T * (S - H - O * T)
12 (A * E - R + A) * (T + O) - R
13 (H * O - N) * (I - T) - O - N
14 H * (O - R - N) * I - S - H
15 E * (S + T * (H + E)) - T - E
16 (H + E * A) * (R + E + R) - S

    """
    import math
    solver = Magpie275()
    clue_list = solver._clue_list
    evaluators = {int(clue.name): clue.evaluators[0] for clue in clue_list}

    letters = "AEHINORST"
    values = [i * i for i in range(1, 10)]
    permutations = [dict(zip(letters, permutation)) for permutation in itertools.permutations(values)]

    for number, evaluator in evaluators.items():
        x = sum(bool(evaluator(permutation)) for permutation in permutations)
        print(number, x, len(evaluator.vars),  x // math.factorial(9 - len(evaluator.vars)))



if __name__ == '__main__':
    # test1()
    Magpie275().run()
