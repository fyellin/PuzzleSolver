import functools
import re
from typing import Dict, Sequence, Pattern, Callable, List, Optional, Tuple, Any

from solver import Clue, ClueValue, Location, Clues, ConstraintSolver, Intersection, Letter
from solver import EquationSolver, KnownClueDict, KnownLetterDict

GRID = """
X.XXXXXXXX
XX.X...X..
.X....X...
X.XXX.XXXX
XX.X.XXX..
X...X..X..
X..X..X...
"""

ACROSS = """
1 (MAR)^C + H (4) (5)
4 COM(E + T) (3) (4)
7 TRIT + O – N (3) (4)
10 CO(M + B) + A + T + S (3) (3)
12 DA(M + E) (3) (4)
13 ROU – T (3) (4)
14 A(NG + S) + T! (3) (4)
15 VIV + A + S (3) (4)
16 INC(U – R + S + I + O + N) + S (3) (4)
18 BANT(E + R – S) – M + E + T (4) (5)
21 TA + R^R + IE + R – S (3) (4)
25 G + O – I + N – G + B + A + N^A + N^(A + S) (3) (4)
28 A(KA + V)A (3) (3)
30 W^(A – S) – O + K (3) (3)
31 A(I + D) + E! (3) (3)
32 COOL – S (3) (4)
33 B^(O – B)SL + E^(I – G) + HT + EA + M (3) (6)
34 NIN + E – S (3) (3)
35 MALT (4) (4)
"""

DOWN = """
1 BBILB + (O + B)(A + G) – GI + N + S (4) (5)
2 WAR(L – O + C + K) (3) (4)
3 R^A – T + (E + N – T + E – R + S)^A(BIN – N) (4) (6)
4 T – O + T + A^I – WAN (3) (4)
5 U – S – E + B^(E – A)N + TI(N + S) (4) (4)
6 L^(E – C) + (T + U + R(E + R) + O/O)M (3) (5)
7 M(A – G – N + E + TI + S)M (4) (5)
8 GL(OB + U – L – E) (3) (4)
9 MARACA + S (3) (4)
11 TALL – M + E – N (3) (4)
17 C^(AR) + N(I + V + A(L + S)) (4) (5)
19 VERV + E – S (4) (4)
20 WRIN + K – L + E + S (4) (4)
22 (R – A)B^A – T (3) (4)
23 B^ANN + TV (4) (5)
24 L(U + M + BE + R + S) (3) (4)
25 MO(O + D) (3) (4)
26 (L + O + G)I^C (3) (4)
27 C^E(R – A + M + I + C) – S (3) (4)
29 T^A (3) (3)
"""


class OuterSolver(EquationSolver):
    @staticmethod
    def run() -> None:
        grid = Clues.get_locations_from_grid(GRID)
        clues = OuterSolver.create_from_text(ACROSS, DOWN, grid)
        solver = OuterSolver(clues)
        for clue in clues:
            if clue.name in ('8d', '24d', '29d'):
                solver.add_constraint([clue], lambda value: value == value[::-1])
            else:
                solver.add_constraint([clue], lambda value: value != value[::-1])
        solver.solve(debug=True)

    @staticmethod
    def create_from_text(across: str, down: str, locations: Sequence[Location]) -> Sequence[Clue]:
        result: List[Clue] = []
        for lines, is_across, letter in ((across, True, 'a'), (down, False, 'd')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (.*) \((\d+)\) \((\d+)\)', line)
                assert match
                number = int(match.group(1))
                location = locations[number - 1]
                clue = Clue(f'{number}{letter}', is_across, location, int(match.group(3)), expression=match.group(2))
                clue.context = int(match.group(4))
                result.append(clue)
        return result


    def __init__(self, clues: Sequence[Clue]):
        super().__init__(clues, items=range(1, 20))

    def make_pattern_generator(self, clue: Clue, intersections: Sequence[Intersection]) -> \
            Callable[[Dict[Clue, ClueValue]], Pattern[str]]:

        assert(all(intersection.this_clue == clue for intersection in intersections))

        if clue.length == clue.context:
            default_item = '[1-9]'
            lookahead = ''
        else:
            default_item = '(1?[1-9]|10)'
            lookahead = f'(?=[0-9]{{{clue.context}}}$)'

        def getter(known_clues: Dict[Clue, ClueValue]) -> Pattern[str]:
            pattern_list = [default_item] * clue.length
            for intersection in intersections:
                other_clue = intersection.other_clue
                pattern = self.get_nth_digit_pattern(other_clue, known_clues[other_clue], intersection.other_index)
                pattern_list[intersection.this_index] = pattern
            pattern = ''.join(pattern_list)
            regexp = lookahead + pattern
            return re.compile(regexp)

        return getter

    @staticmethod
    def get_nth_digit_pattern(clue: Clue, value: str, index: int) -> str:
        # Shortcut.  A normal clue in which only one letter can go into each square
        if clue.context == clue.length:
            return value[index]
        parsings = OuterSolver.parse_with_pairs(clue.context - clue.length, value)
        results = {parse[index] for parse in parsings}
        return  '(' + '|'.join(results) + ')'

    @staticmethod
    @functools.lru_cache(None)
    def parse_with_pairs(pairs: int, value: str) -> List[Tuple[str, ...]]:
        if pairs == 0:
            return [tuple(value)]
        if value == '' or value[0] == '0':
            return []
        start = value[0]
        result = [(start,) + x for x in OuterSolver.parse_with_pairs(pairs, value[1:])]
        if value[0] == '1':
            start = value[0:2]
            result.extend((start,) + x for x in OuterSolver.parse_with_pairs(pairs - 1, value[2:]))
        return result


    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        print(tuple((letter, value) for letter, value in known_letters.items()))
        print(tuple((clue.name, value) for clue, value in known_clues.items()))
        self.show_letter_values(known_letters)
        InnerSolver.run(self._clue_list, known_clues, known_letters)


class InnerSolver(ConstraintSolver):
    clue_values: KnownClueDict
    letter_values: KnownLetterDict

    @staticmethod
    def run(clue_list: Sequence[Clue], clue_values: KnownClueDict, letter_values: KnownLetterDict) -> None:
        solver = InnerSolver(clue_list, clue_values, letter_values)
        solver.solve(debug=True)

    @staticmethod
    def test() -> None:
        letters = (('A', 3), ('T', 7), ('K', 18), ('V', 17), ('B', 10), ('R', 5), ('N', 9), ('L', 11), ('M', 19),
                   ('E', 6), ('S', 1), ('I', 8), ('W', 13), ('G', 4), ('D', 15), ('C', 2), ('O', 14), ('U', 16),
                   ('H', 12))
        print(', '.join(x for x, _ in letters), '=', ', '.join(str(x) for _, x in letters))
        letter_values = {Letter(letter): value for letter, value in letters}
        grid = Clues.get_locations_from_grid(GRID)
        clues = OuterSolver.create_from_text(ACROSS, DOWN, grid)
        clue_values: KnownClueDict = {clue: clue.evaluators[0](letter_values) for clue in clues}
        solver = InnerSolver(clues, clue_values, letter_values)
        solver.solve(debug=True)

    def __init__(self, clue_list: Sequence[Clue], clue_values: KnownClueDict, letter_values: KnownLetterDict):
        super().__init__(clue_list)
        for clue in clue_list:
            clue.generator = self.generator
        self.clue_values = clue_values
        self.letter_values = letter_values

    def generator(self, clue: Clue) -> Sequence[str]:
        value = self.clue_values[clue]  # The calculated value of this clue (as a string)
        parsings = OuterSolver.parse_with_pairs(clue.context - clue.length, value)
        for parsing in parsings:
            result = [chr(int(digit) + 48) for digit in parsing]
            yield ''.join(result)

    def draw_grid(self, **args: Any) -> None:
        location_to_entry: Dict[Location, str] = args['location_to_entry']
        args['location_to_entry'] = {location : str(ord(code) - 48) for location, code in location_to_entry.items()}
        super().draw_grid(**args)

        mapping = { value: letter for letter, value in self.letter_values.items() }
        args['location_to_entry'] = {location : mapping[ord(code) - 48] for location, code in location_to_entry.items()}
        super().draw_grid(**args)


if __name__ == '__main__':
    InnerSolver.test()
