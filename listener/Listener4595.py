import itertools
from fractions import Fraction
from typing import Dict, Sequence, Iterable, FrozenSet, Set

from solver import Clue, Clues
from solver import EquationSolver
from solver.equation_solver import KnownLetterDict

GRID = """
XX.XXXXX
X..X.X..
.XX.XX..
XX.XX.XX
X..X.X..
X....X..
"""

ACROSS = """
1 A + F (3) 
5 L + N + U (3) 
8 A (3) 
9 M − s (2) 
10 os + R (3) 
11 e + n + S (3) 
13 D + i + N (3) 
16  (3) 
18 D + S (3) 
21 tU + E − M (3) 
22 F + H − O (2) 
23 Is − A − H (3) 
24 A + o + P − R (3) 
25 C + i + t − L (3)
"""

DOWN = """
1 A + M + N + N (3) 
2 T − n (3) 
3 OO + H + W (3) 
4 T (3) 
6 e + I + T (3) 
7 i + N (3) 
12 P (2) 
14 s + s + U (2) 
15 D + W − o (3) 
16 F + I + i + M (3) 
17 L + W − o (3) 
18 FU + e + P (3) 
19 H + P + P (3) 
20 L − D − I (3)
"""

POWER_TO_LETTER = {
    2: "AELNoRsTtUW",
    3: "enOS",
    4: "iMP",
    5: "FI",
    6: "CH",
    8: "D"
}

LETTER_TO_POWER = {
    letter: power
    for power, letters in POWER_TO_LETTER.items()
    for letter in letters
}

SOLUTION = dict(s=4, U=9, M=16,
                O=27, F=32,
                N=36, t=49, H=64,
                P=81,  o=100, W=121, e=125, R=196, S=216,
                I=243, D=256, E=289, n=343, T=529, i=625, C=729, A=784, L=841)

ENDGAME = """
1a, 5a, 4d
8a, 14d, 20d
9a, 10a, 24a
11a, 13a, 19d
18a, 22a, 17d
21a, 7d, 16d
23a, 25a, 6d
1d, 12d, 18d
2d, 3d, 15d
"""


class OuterSolver(EquationSolver):
    power_to_values: Dict[int, FrozenSet[int]]

    @staticmethod
    def run() -> None:
        grid = Clues.get_locations_from_grid(GRID)
        clues = Clues.create_from_text(ACROSS, DOWN, grid)
        solver = OuterSolver(clues)
        solver.solve(debug=True)

        answers = {clue: clue.evaluators[0](SOLUTION) for clue in clues if clue.evaluators}
        items = []
        for line in ENDGAME.strip().splitlines():
            group = []
            for clue_name in line.split(', '):
                clue = solver.clue_named(clue_name)
                value = answers[clue]
                assert value
                group.append(Fraction(int(value)))
                group.append(Fraction(918 - int(value)))
            items.append(group)

        def sum_power(values: Sequence[Fraction], power: int) -> int:
            return sum(v ** power for v in values)

        def all_sum_power(power: int) -> Sequence[int]:
            return [sum_power(item, power) for item in items]

        for p in range(-10, 10):
            temp = all_sum_power(p)
            if all(temp[0] == x for x in temp):
                print(p, temp[0])
        print(all_sum_power(-1))

    def __init__(self, clues: Sequence[Clue]):
        self.power_to_values = self.__get_values()
        all_values = {value for values in self.power_to_values.values() for value in values}
        super().__init__(clues, items=sorted(all_values))

    def get_letter_values(self, known_letters: KnownLetterDict, letters: Sequence[str]) -> Iterable[Sequence[int]]:
        powers = [LETTER_TO_POWER[letter] for letter in letters]
        ok_values = [self.power_to_values[power] for power in powers]
        for result in super().get_letter_values(known_letters, letters):
            if all(x in y for x, y in zip(result, ok_values)):
                yield result

    @staticmethod
    def __get_values() -> Dict[int, FrozenSet[int]]:
        temp: Dict[int, Set[int]] = {}
        for power in (2, 3, 4, 5, 6, 8):
            temp[power] = set(itertools.takewhile(lambda x: x < 1000, (i ** power for i in itertools.count(2))))
        temp[2] -= temp[4]
        temp[2] -= temp[6]
        temp[2] -= temp[8]
        temp[3] -= temp[6]
        temp[4] -= temp[8]
        return {power: frozenset(sorted(info)) for power, info in temp.items()}


if __name__ == '__main__':
    OuterSolver.run()
