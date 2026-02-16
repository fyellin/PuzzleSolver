import re
from typing import cast
from collections.abc import Sequence, Iterable

from solver import Clue, Clues, EquationSolver, Letter, ClueValue
from solver import KnownClueDict, KnownLetterDict

GRID = """
X.X..XXX..XXX
X....X....X..
.X.X....X.X.X
X......X.....
..X..XX......
X......X..XX.
....X.......X
X...X..X.X...
......X......
..X..X.......
XX.....X.XX.X
X.X.......X..
X..X...X...X.
"""

# Note.  Double quotes indicate concatenation!
ACROSS = """
1 N + S + L (2)
2 WOW (4)
4 FF (4)
6 NO + VE (3)
9 L(E + TT + E + R – S) (3)
10 Q(UES + TIO + N + NA + IR – E + S) + Q(U + ES + T) (6)
12 HO + P (3)
15 J + A + C + K + J + A + C + K + Y  + 12 (3)
18 (A + N + G + R)Y + A + L + F – MOM (4)
19 H(A – T + C)H + E – R – S (5)
22 T – U + (X + E)DO (4)
23 D + O + D + R – I – P (2)
24 “OU” (3)
26 “ATOM” (5)
28 S + HEM + O – ZZ + LES + TO(E + S) (3)
29 PM – COS (2)
31 E + QU – I + T – A – B – L + E (4)
32 (P + E + R + U + V)I(A – N) (5)
33 NN/E (4)
35 TED (3)
38 (DR – SO(R + E))(DR – SO(R + E)) – SO – SO (3)
42 “AWN” (6)
43 (ME + L)D (3)
44 MEW + T + EE + MS (3)
45 NN (4)
46 MEW + T + A + MS (4)
47 49 - 3 (2)
"""

DOWN = """
1 N(O + B + L + E) – NOT – NO (3)
2 (PE – CK)(PE – CK) (3)
3 PT (3)
5 (E + S + S + E)X + (P + A)X - 3 (4)
7 CVY + V (3)
8 A – EE (2)
11 (JO – Y)S (3)
12 “XYZ” (6)
13 UK(E + S) (4)
14 (E + R)(Y + T(H + R + O) + P + US) (5)
16 (C + U)FF – (B + I)FF + 12 (4)
17 “ZX” (4)
20 F (2)
21 NOON + MOW (5)
25 EQUI + TA + B – L + E (6)
26 CORMS – FEME (5)
27 DE + NI + (Z + E)N (4)
28 “PC” (4)
30 S + I – M (2)
31 RIL(E – S) (4)
33 NO – MOO (3)
34 WOWS (4)
36 A + A (3)
37 MOW (3)
39 (V + OE)(V + OE) – MOS – MOS (3)
40 GI – ODD (3)
41 MM (2)
"""



class MySolver(EquationSolver):
    def get_letter_values(self, known_letters: dict[Letter, int], letters: Sequence[str]) -> Iterable[Sequence[int]]:
        """
        Returns the values that can be assigned to the next "count" variables.  We know that we have already assigned
        values to the variables indicated in known_letters.
        """
        count = len(letters)
        assert count <= 1
        if count == 0 or count >= 2 or letters[0] not in 'TOM':
            temp = list(super().get_letter_values(known_letters, letters))
            yield from temp
            return
        for i in range(2, 10):
            if i not in set(known_letters.values()):
                yield i,

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        pass


def create_clue_list(alt: bool = False) -> Sequence[Clue]:
    locations = Clues.get_locations_from_grid(GRID)
    result: list[Clue] = []
    for lines, is_across, letter in ((ACROSS, True, 'a'), (DOWN, False, 'd')):
        for line in lines.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
            assert match
            number = int(match.group(1))
            expression = match.group(2)
            location = locations[number - 1]
            if '”' in expression:
                if alt:
                    expression = '+'.join(f'str({ch})' for ch in expression[1:-1])
                    expression = f'@ int({expression})'
                    clue = Clue(f'{number}{letter}', is_across, location, int(match.group(3)), expression=expression)
                    result.append(clue)
                else:
                    for ch in expression[1:-1]:
                        length = 1 if ch in 'TOM' else 2
                        clue = Clue(f'{number}{ch}{letter}', is_across, location, length, expression=ch)
                        result.append(clue)
                        (row, column) = location
                        location = (row, column + length) if is_across else (row + length, column)
            else:
                if not alt and number == 47:
                    clue = Clue(f'{number}{letter}', is_across, location, int(match.group(3)))
                elif not alt and number in (5, 15, 16):
                    continue
                else:
                    clue = Clue(f'{number}{letter}', is_across, location, int(match.group(3)), expression=expression)
                result.append(clue)
    return result


def run() -> None:
    clue_list = create_clue_list()
    solver = MySolver(clue_list, items=list(range(2, 100)), allow_duplicates=True)
    # solver.verify_is_four_fold_symmetric()
    solver.solve(debug=True)


def run2() -> None:
    clue_list = create_clue_list(True)
    letters = [Letter(x) for x in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"]
    values = (98, 30, 19, 17, 6, 57, 39, 24, 27, 32, 13, 2, 7, 84, 3, 43, 71, 53, 5, 9, 40, 4, 21, 15, 10, 31)
    assert len(letters) == len(values) == 26
    solver = MySolver(clue_list, items=list(range(2, 100)))
    letter_values = dict(zip(letters, values))
    clue_values = {clue: cast(ClueValue, clue.evaluators[0](letter_values)) for clue in clue_list}
    print(len(clue_values.values()))
    print(len(set(clue_values.values())))
    solver.plot_board(clue_values)

# L  O  V  S  E  M  T  Y  K  X  D  C  W  H  I  B  Z  J  G  U  P  R  F  Q  N  A
# 2  3  4  5  6  7  9  10 13 15 17 19 21 24 27 30 31 32 39 40 43 53 57 71 84 98

# 98 17 17 9 21 6 2 4 6   ADD TWELVE
# 9 98 13 6   9 24 53 6 6  TAKE THREE

# 39,932,495


if __name__ == '__main__':
    run()
