import itertools
import re
from collections.abc import Iterable, Sequence

from solver import Clue, Clues, EquationSolver, Evaluator, KnownLetterDict

GRID = """
XX.XX.X
X..X...
.XX.X..
X.X..XX
X..XXX.
.XX.X..
X..X...
"""

ACROSS = """
2 C–H                     (3)
4 (T+E+R–M–I)NI           (3)
6 CH^H                    (3)
7 YT                      (3)
8 E(R–N)E–(P+O+S–I–T+I)ON (2)
10 Y–T                    (3)
11 HS^S                   (2)
12 COM–POSE–R + ANNI–V+E–R+S–ARY (3)
13 H–S                 (2)
15 I–H                 (3)
17 (C–O+RR/E)^(C – T) + T–H+E – STAR+TS (2)
19 IH                  (3)
21 NH^H                (3)
22 (AT(O–M)+I)/C + NO  (3)
23 N^N–H^N             (3)
"""

DOWN = """
1 NU + T,           T + N + U  (4)
2 (I–C)^N,          N(√ I)!–C  (3)
3 HP–A,             A^H –P     (3)
4 (R / (E – A))!,   AR/E       (2)
5 C - AS,           A(C-S)     (3)
9 O-R + U,          (U-O)R     (3)
10 NSH,             (N!-S)H    (3)
14 O + (N + S)!,    NOS        (4)
15 T + V - N!,      V-N-T      (3)
16 HU - M,          U + M + H  (3)
18 (R–E)!–√ I,      E + R - I  (3)
20 N!/(I-C),         N-C+I      (2)
"""


class Magpie240(EquationSolver):
    @staticmethod
    def run() -> None:
        solver = Magpie240()
        solver.verify_is_180_symmetric()
        solver.solve(debug=False,  multiprocessing=False)

    def __init__(self):
        clues = self.get_clues()
        super().__init__(clues, items=())

    def get_clues(self):
        locations = Clues.get_locations_from_grid(GRID)
        results = []
        for lines, is_across, letter in ((ACROSS, True, 'a'), (DOWN, False, 'd')):
            rexp = r'(\d+) (.*) \((\d+)\)' if is_across else r'(\d+) (.*), (.*) \((\d+)\)'
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(rexp, line)
                assert match
                number = int(match.group(1))
                location = locations[number - 1]
                length = int(match.group(4 - is_across))
                expr1 = match.group(2).strip()
                expr2 = f'$a{number} - 100' if is_across else match.group(3).strip()
                clue = Clue(f'{number}{letter}', is_across, location, length)
                expression = f'@square2({expr1}, {expr2})'
                clue.evaluators = Evaluator.create_evaluators(
                    expression, mapping={'square2': self.squares2})
                results.append(clue)
        # self.across_clues = [clue for clue in results if clue.is_across]
        # self.down_clues = [clue for clue in results if not clue.is_across]
        return results

    @staticmethod
    def squares2(a, b):
        if a < 0 or b < 0 or a > 100 or b > 100:
            return -1
        if (int_a := int(a)) != a or (int_b := int(b)) != b:
            return -1
        return int_a * int_a + int_b * int_b

    def get_letter_values(
            self, known_letters: KnownLetterDict, letters: Sequence[str]
    ) -> Iterable[Sequence[int]]:
        if not letters:
            yield()
            return
        uppers = [x for x in letters if len(x) == 1 and x.isupper()]
        downers = [x for x in letters if len(x) > 1 or x.islower()]
        unused_uppers = unused_downers = []
        if uppers:
            unused_uppers = [i for i in range(1, 16)
                             if i not in known_letters.values()]
        if downers:
            unused_downers = [i for i in range(101, 200)
                              if i not in known_letters.values()]
        if not downers:
            for values in itertools.permutations(unused_uppers, len(uppers)):
                yield values
        elif not uppers:
            for value in unused_downers:
                yield value,
        else:
            for values in itertools.permutations(unused_uppers, len(uppers)):
                for value in unused_downers:
                    yield *values, value


if __name__ == '__main__':
    Magpie240.run()
