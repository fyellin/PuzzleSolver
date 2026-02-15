import itertools
import re
from collections.abc import Sequence
from graphlib import TopologicalSorter
from typing import Any

from solver import Clue, Clues, EquationSolver
from solver import KnownClueDict, KnownLetterDict

ACROSS_LENGTHS = "3132/13311/333/333/333/11331/2313"
DOWN_LENGTHS = "313/331/11113/331/313/133/31111/133/313"

CLUES = """
29ac I + I + I
6ac hhh
19ac hh + II + a
16dn in − R
28ac in + L
19dn C + I + N
24ac r − e − h
23dn O + o + s
10dn aaa + aI
2dn m − L
17ac aaa + C
31ac at − T
9ac hhI + u
20dn U − L
27ac i + p + s + s
17dn Rt − f
7dn ii + nR
4dn c + c + h
12ac iN + a
4ac F + N + N + u
22dn a + y
30ac L + n + y
26dn n + S + y
11dn aO + hO
14ac aL + b
21ac f + o + o − s
13ac a + b + F + F
8ac III + L + L
1ac b + i + i + p
1dn E + u − T
5dn LL + LL + h
3dn hhS + L
25dn ar − af
"""


class Listener4882(EquationSolver):
    @classmethod
    def run(cls) -> None:
        solver = cls()
        # solver.plot_board()
        # solver.verify_is_180_symmetric()
        solver.solve(debug=True)

    def __init__(self):
        values = self.get_clue_values()
        clue_list = self.get_clues()
        super().__init__(clue_list, items=values)
        for clue1, clue2 in itertools.combinations(clue_list[:-2], 2):
            self.add_constraint((clue1, clue2), lambda x, y: int(x) < int(y))

    def get_clues(self) -> Sequence[Clue]:
        clue_dict = Clues.clue_info_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        clues = []
        for line in CLUES.strip().splitlines():
            match = re.fullmatch(r"(\d+)(ac|dn) (.*)", line)
            number = int(match.group(1))
            assert match.group(2) in ('ac', 'dn')
            is_across = match.group(2) == 'ac'
            name, start, length = clue_dict.pop((number, is_across))
            clues.append(Clue(name, is_across, start, length, expression=match.group(3)))
        for (_, is_across), (name, start, length) in clue_dict.items():
            expression = None
            clues.append(Clue(name, is_across, start, length, expression=expression))
        return clues

    def show_solution(self, known_clues: KnownClueDict,
                      known_letters: KnownLetterDict) -> None:
        known_clues = known_clues.copy()
        known_clues[self.clue_named('15a')] = '311'
        known_clues[self.clue_named('18a')] = '207'
        super().show_solution(known_clues, known_letters)

    def plot_board(self, known_clues: KnownClueDict | None = None,
                   known_letters: KnownLetterDict | None = None, **more_args: Any) -> None:
        if not known_clues or True:
            super().plot_board(known_clues, **more_args)

        self.print_message(known_letters)

        triples = [value for clue, value in known_clues.items() if clue.length == 3]

        def get_next(x):
            return str(int(x) ** 3)[0:3]

        ts = TopologicalSorter()
        result = []
        for value in triples:
            ts.add(get_next(value), value)
        ts.prepare()
        while ts.is_active():
            next_value, = ts.get_ready()
            result.append(int(next_value))
            ts.done(next_value)
        print(result)
        first_value = result[0]

        assert len(triples) == 33
        assert len(known_letters) == 27
        sum_of_terms = sum(map(int, triples))
        sum_of_letter_values = sum(known_letters.values())

        first_clue, = [clue for clue, value in known_clues.items() if value == str(first_value)]

        shading = dict.fromkeys(first_clue.locations, 'lightgreen')
        subtext = (f'∑ terms: {str(sum_of_terms)[:3]}\n'
                   f'∑ letter values: {str(sum_of_letter_values)[:3]}\n')
        print(sum_of_terms, sum_of_letter_values)
        import math
        print(math.cbrt(sum_of_terms), math.cbrt(sum_of_letter_values))

        super().plot_board(known_clues, shading=shading, subtext=subtext, **more_args)

    def print_message(self, known_letters):
        pairs = [(value, letter) for letter, value in known_letters.items()]
        pairs.sort()
        letters = ''.join(x for _, x in pairs)
        print(letters[0::3], letters[1::3], letters[2::3])

    def get_clue_values(self):
        result = set()
        for i in itertools.count(3, 3):
            square = i * i
            if square < 1000:
                continue
            if square > 9999:
                break
            string = str(square)
            for j in range(3):
                if string[~j] != '0':
                    result.add(int(string[~j:]))
        return sorted(result)


if __name__ == '__main__':
    Listener4882.run()
