import itertools
import re
from typing import Sequence, Set, Dict, Any, Match, Iterator, Tuple, cast

from solver import Clue, ConstraintSolver, Location, Clues, ClueValue
from solver.equation_solver import KnownClueDict

GRID = """
XXXXXXX
X..X.X.
XXXXXX.
X.X..X.
X..XXXX
XXXXXX.
X..X.X.
"""

ACROSS = """
1 2 + 7 (2)
3 13 + 19 (2)
5 7 + 21 + 34 + 57 (3)
8 2 + 5 (3)
9 2 + 24 + 31 (2)
10 2 + 2 + 30 (2)
11 3 + 10 + 15 (2)
13 3 + 5 + 15 (2)
15 13 + 15 + 15 (3)
17 2 + 3 + 23 (2)
18 12 + 21 + 187 (3)
19 3 + 11 + 31 (2)
20 3 + 28 + 40 (3)
21 7 + 13 (2)
23 17 + 21 + 33 (2)
25 2 + 2 + 7 (2)
27 2 + 47 (2)
29 2 + 23 + 31 (3)
31 28 – 5 (3)
32 3 + 13 (2)
33 2 + 12 + 17 (2)
"""

DOWN = """
1 12 – 3 – 17 (3)
2 2 + 22 + 44 (2)
3 3 + 21 + 38 (3)
4 2 + 18 – 10 (2)
5 13 + 15 + 17 (2)
6 2 + 5 – 11 (2)
7 12 + 42 + 365 (4)
12 14 + 30 + 52 (3)
14 2 + 7 + 28 + 48 (3)
15 2 + 3 + 17 (2)
16 2 – 12 – 38 (3)
17 3 + 22 + 1249 (4)
18 5 + 14 + 14 (2)
22 2 + 23 – 7 (3)
24 6 + 13 + 658 (3)
26 15 + 45 – 3 (2)
27 2 + 3 + 6 (2)
28 2 + 2 + 7 (2)
30 2 + 33 (2) 
"""


class Solver205(ConstraintSolver):
    def __init__(self) -> None:
        super().__init__(self.make_clue_list())
        self.generator_dict: Dict[Tuple[Clue, str], Tuple[Sequence[int], int]] = {}

    def draw_grid(self, max_row: int, max_column: int, clued_locations: Set[Location],
                  location_to_entry: Dict[Location, str], location_to_clue_number: Dict[Location, str],
                  top_bars: Set[Location], left_bars: Set[Location], **more_args: Any) -> None:
        temp = {location: str(ord(value) - 48) for location, value in location_to_entry.items()}
        shading = {location: 'lightblue' for location, value in temp.items() if value == '3'}
        super().draw_grid(max_row, max_column, clued_locations, temp, location_to_clue_number, top_bars,
                          left_bars, shading=shading, **more_args)
        temp2 = {location: int(value) for location, value in temp.items()}
        for i in range(1, 8):
            a = sum(value**3 for (x, y), value in temp2.items() if x == i)
            b = sum(value**3 for (x, y), value in temp2.items() if y == i)
            print(i, a, b)
        c = sum(value ** 3 for (x, y), value in temp2.items() if x == y)
        d = sum(value ** 3 for (x, y), value in temp2.items() if x + y == 8)
        print(c, d)

    def show_solution(self, known_clues: KnownClueDict) -> None:
        super().show_solution(known_clues)
        for clue in self._clue_list:
            value = known_clues[clue]
            powers, real_value = self.generator_dict[clue, value]
            expression = clue.expression
            for var, power in zip(clue.evaluators[0].vars, powers):
                expression = expression.replace(var, str(power))
            print(f'{clue.name}:  {expression} = {real_value}')

    def make_clue_list(self) -> Sequence[Clue]:
        locations = Clues.get_locations_from_grid(GRID)
        clues = []
        for lines, is_across, letter in ((ACROSS, True, 'a'), (DOWN, False, 'd')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
                assert match
                number = int(match.group(1))
                equation = match.group(2)
                length = int(match.group(3))
                location = locations[number - 1]

                # Put an exponent (e.g. **a, **b, **c) after each number.
                def replacer(xmatch: Match[str]) -> str:
                    variable = chr(xmatch.end(0) + ord('A'))
                    return xmatch.group(0) + '**' + variable

                equation = re.sub(r'(\d+)', replacer, equation)
                clue = Clue(f'{number}{letter}', is_across, location, length, expression=equation,
                            generator=self.generator)
                clues.append(clue)
        return clues

    def generator(self, clue: Clue) -> Iterator[str]:
        min_size = 10 ** (clue.length - 1)
        max_size = 10 ** (2 * clue.length)
        evaluator = clue.evaluators[0]
        seen: Set[ClueValue] = set()

        max_power = 20 if "–" in clue.expression else 16

        for powers in itertools.product(range(2, max_power + 1), repeat=len(evaluator.vars)):
            dictionary = dict(zip(evaluator.vars, powers))
            value = evaluator(dictionary)
            if value is not None and min_size <= int(value) < max_size and value not in seen:
                seen.add(value)
                # pair_count is the number of double digits we'll require
                pair_count = len(value) - clue.length
                for pairs in itertools.combinations(range(clue.length), pair_count):
                    copy_value = cast(str, value)
                    result = []
                    for i in range(clue.length):
                        size = 2 if i in pairs else 1
                        result.append(copy_value[:size])
                        copy_value = copy_value[size:]
                    # We don't allow any of the two-digit entries to start with a zero.
                    if any(len(digits) == 2 and digits[0] == '0' for digits in result):
                        continue
                    assert len(copy_value) == 0
                    # Just use the 99 ascii characters starting at '0'.  Good enough
                    code = ''.join(chr(48 + int(digits)) for digits in result)
                    self.generator_dict[clue, code] = (powers, int(value))
                    yield code


def run() -> None:
    solver = Solver205()
    solver.verify_is_180_symmetric()
    solver.solve()


if __name__ == '__main__':
    run()
