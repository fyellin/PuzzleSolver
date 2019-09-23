import re
from typing import Dict, Iterable, List, Tuple, Set, Any

from Clue import Clue
from ClueList import ClueList
from ClueTypes import Location, ClueValue, Letter
from EquationSolver import EquationSolver

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


class MyClue(Clue):
    def generate_location_list(self) -> Iterable[Location]:
        if self.name[-1] == 'd':
            return super().generate_location_list()
        elif self.name[-1] == 't':
            (row, column) = self.base_location
            return ((row + 4 * i, column) for i in range(self.length))
        elif self.name[-1] == 'a':
            locations = super().generate_location_list()
            return [(row + ((column - 1) // 4) * 4, ((column - 1) % 4) + 1) for (row, column) in locations]
        else:
            assert False


class MyClueList(ClueList):
    def draw_grid(self, max_row: int, max_column: int, clued_locations: Set[Location],
                  location_to_entry: Dict[Location, str], location_to_clue_number: Dict[Location, str],
                  top_bars: Set[Location], left_bars: Set[Location], **more_args: Any) -> None:
        # The only thick bars we want are between each of the sections.
        left_bars.clear()
        top_bars = {(row, column) for row in (5, 9, 13) for column in (1, 2, 3, 4)}
        super().draw_grid(max_row, max_column, clued_locations, location_to_entry, location_to_clue_number,
                          top_bars, left_bars, **more_args)
        # Now draw the grid using the secret word.
        location_to_entry = {location: 'DEPILATORS'[int(value)] for (location, value) in location_to_entry.items()}
        super().draw_grid(max_row, max_column, clued_locations, location_to_entry, location_to_clue_number,
                          top_bars, left_bars, **more_args)


class MySolver (EquationSolver):
    good_values: Tuple[int, ...]

    def __init__(self, clue_list: ClueList) -> None:
        super().__init__(clue_list, items=MySolver.get_clue_values())
        self.good_values = tuple(self.get_clue_values())

    def show_solution(self,  known_clues: Dict[Clue, ClueValue], known_letters: Dict[Letter, int]) -> None:
        super().show_solution(known_clues, known_letters)
        for clue in self.clue_list:
            print(clue.name, known_clues[clue])

    @staticmethod
    def get_clue_values() -> List[int]:
        result = set()
        for i in range(3, 47):
            cube = i * i * i
            temp = int(str(cube)[1:])
            result.add(temp)
        result.remove(0)
        return sorted(result)


def create_clue_list() -> 'ClueList':
    locations = [(0, 0)]
    for row, line in enumerate(GRID.split()):
        for column, item in enumerate(line):
            if item == 'X':
                locations.append((row + 1, column + 1))

    result: List[Clue] = []
    for lines, is_across, letter in ((ACROSS, True, 'a'), (DOWN, False, 'd'), (THROUGH, False, 't')):
        for line in lines.splitlines():
            line = line.strip()
            if not line:
                continue
            match = re.fullmatch(r'(\d+) (.*) \((\d+)\)', line)
            assert match
            number = int(match.group(1))
            location = locations[number]
            expression = match.group(2)
            clue = MyClue(f'{number}{letter}', is_across, location, int(match.group(3)), expression=expression)
            result.append(clue)
    return MyClueList(result)


def run() -> None:
    clue_list = create_clue_list()
    solver = MySolver(clue_list)
    solver.solve()


if __name__ == '__main__':
    run()
