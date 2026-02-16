import re
from collections.abc import Sequence
from typing import Any

from solver import Clue, ClueValue, KnownClueDict, KnownLetterDict, Letter, Location
from solver import EquationSolver

ACROSS = """
1 GS − Gz − S (6)
2 S − I − LL (3)
5 a + NW − N (6) 
7 dd + OO − u (6) 
9 CZZ − i − Z (6)
10 C + LL + T (4)
12 CU − UU (5)
13 r − A − Z − O + r (4)
14 iIz + Iz (7)
15 El + e + e + e (6) 
16 PR − A + P + P (6)
19 C − LL (4)
20 LL + R + z (4)
"""

DOWN = """
2 DU + UU + o (5) 
3 B + ir − i − r (6) 
6 ii + i − T − W (4)
10 No − C + N (6) 
11 LN − L + TT (6)
13 eT + e − T − T (7) 
14 NU + ZZ (4)
17 E − pp (3)
18 dO − O + T (6)
"""

THROUGH = """
2 Lpp + Z (3) 
4 UUU (3)
8 Uz − pp (3)
14 pz + z + L (3)
"""

GRID = """
X...
XX.X
X.X.
X..X
X.X.
X..X
..XX
X...
..X.
...X
..X.
....
....
X....
....
X...
"""


class MySolver (EquationSolver):
    def __init__(self, clue_list: Sequence[Clue]) -> None:
        super().__init__(clue_list, items=MySolver.get_clue_values())


    def show_solution(self,  known_clues: KnownClueDict, known_letters: KnownLetterDict
                      ) -> None:
        super().show_solution(known_clues, known_letters)
        for clue in self._clue_list:
            print(clue.name, known_clues[clue])

    def draw_grid(self, **args: Any) -> None:
        # The only thick bars we want are between each of the sections.
        args['left_bars'] = set()
        args['top_bars'] = {(row, column) for row in (5, 9, 13) for column in (1, 2, 3, 4)}
        super().draw_grid(**args)
        # Now draw the grid using the secret word.

        location_to_entry: dict[Location, str] = args['location_to_entry']
        location_to_entry = {location: 'DEPILATORS'[int(value)] for (location, value) in location_to_entry.items()}
        args['location_to_entry'] = location_to_entry
        super().draw_grid(**args)

    @staticmethod
    def get_clue_values() -> list[int]:
        result = set()
        for i in range(3, 47):
            cube = i * i * i
            temp = int(str(cube)[1:])
            result.add(temp)
        result.remove(0)
        return sorted(result)


def create_clue_list() -> Sequence[Clue]:
    locations = [(0, 0)]
    for row, line in enumerate(GRID.split()):
        for column, item in enumerate(line):
            if item == 'X':
                locations.append((row + 1, column + 1))

    result: list[Clue] = []
    for lines, is_across, suffix in ((ACROSS, True, 'a'), (DOWN, False, 'd'), (THROUGH, False, 't')):
        for line in lines.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
            assert match
            number = int(match.group(1))
            location = locations[number]
            expression = match.group(2)
            length = int(match.group(3))

            row, column = location
            if suffix == 'd':
                location_list = [(row + i, column) for i in range(length)]
            elif suffix == 't':
                location_list = [(row + 4 * i, column) for i in range(length)]
            elif suffix == 'a':
                temp = [(row, column + i) for i in range(length)]
                location_list = [(row + ((column - 1) // 4) * 4, ((column - 1) % 4) + 1) for (row, column) in temp]
            else:
                assert False

            clue = Clue(f'{number}{suffix}', is_across, location, length, expression=expression,
                        locations=location_list)
            result.append(clue)
    return result


def run() -> None:
    clue_list = create_clue_list()
    solver = MySolver(clue_list)
    solver.solve()


if __name__ == '__main__':
    run()
