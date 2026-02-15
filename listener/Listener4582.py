import re
from os.path import commonprefix
from typing import Dict, Set, Any, Sequence, Pattern, Callable, List

from solver import Clue, ClueValue, Location, Clues, ConstraintSolver, Intersection, Letter
from solver import EquationSolver, KnownClueDict, KnownLetterDict

# An X marks were the numbered squares are
GRID = """
XX.XXXXXX.XX
X.X.X....X..
X....X..X...
XX..XX.XX..X
X..XX.XX..X.
X..X....X...
X.....X.....
"""

# This is just copied from the puzzle.
ACROSS = """
1 AAA + AA (6)
6 AARRR − GGI (6)
11 NRT + A (4)
13 GIIII + I (5)
14 EEE + HHH + SSS (3)
15 DLTT − GR (5)
16 GHS (3)
17 EEENN + L (4)
18 DS(II − E) (4)
20 TT(S + T) + T + L (4)
23 AHNN + R (4)
25 L(A + D + I) (4)
27 I(D + H + R) (3)
29 RRRR − RRR − RR − R (5)
31 ENR (3)
32 ATT (5)
33 LLL + LL (4)
34 DLNT + E (6)
35 ADLST − EII (6)
"""

DOWN = """
1 N(IL + T) (4)
2 LN (3)
3 LL(A + I + S) − R (4)
4 AA + R (4)
5 HH + NN (3)
6 TTT − L (4)
7 LR + E (3)
8 D + T (3)
9 AE(SD − H) (4)
10 LS (3)
12 (EGHIR − S)(N + L + R) (5)
14 DEGHST + A + R (5)
19 I(GGI − A) (4)
21 DDR + A (4)
22 TT + E (4)
23 EEE + HHH + III (4)
24 EGHIN (4)
25 SS + S (3)
26 NN + N (3)
27 HHH + III − SSS (3)
28 DG − T (3)
30 HHH + NNN + SSS (3)
"""


class OuterSolver(EquationSolver):
    @staticmethod
    def run() -> None:
        locations = Clues.get_locations_from_grid(GRID)
        clue_list = Clues.create_from_text(ACROSS, DOWN, locations)
        solver = OuterSolver(clue_list, items=range(1, 12))
        solver.verify_is_180_symmetric()
        solver.solve()

    # Normally, this method generates a function that when called with the actual values of the already
    # known clues, returns a pattern. That pattern should only match a potential value of "clue" if it is the right
    # length, intersects previously entered clues correctly, and doesn't have a 0 where it doesn't belong.
    #
    # We don't care about any of that.  We just want to make sure the potential value for "clue" has a length
    # that is either 1 or 2 less than clue.length.  The values of already known clues and intersections is irrelevant
    def make_pattern_generator(self, clue: Clue, intersections: Sequence[Intersection]) -> \
            Callable[[Dict[Clue, ClueValue]], Pattern[str]]:
        pattern_string = f'.{{{clue.length - 2},{clue.length - 1}}}'   # e.g.  r'.{3,4}' if clue.length == 5.
        pattern = re.compile(pattern_string)
        return lambda _: pattern

    # Normally, this method is called to show the solution.  We want it to call the other solver with what we know
    # now are the values.
    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        self.show_letter_values(known_letters)
        InnerSolver.run(self._clue_list, known_clues, known_letters)


class InnerSolver(ConstraintSolver):
    clue_values: KnownClueDict
    letter_values: KnownLetterDict

    @staticmethod
    def run(clue_list: Sequence[Clue], clue_values: KnownClueDict, letter_values: KnownLetterDict) -> None:
        solver = InnerSolver(clue_list, clue_values, letter_values)
        solver.solve(debug=False)

    @staticmethod
    def test() -> None:
        # For testing this class on its own, without needing OuterSolver
        locations = Clues.get_locations_from_grid(GRID)
        clue_list = Clues.create_from_text(ACROSS, DOWN, locations)
        solution = {'H': 1, 'E': 2, 'S': 3, 'N': 4,  'I': 5, 'G': 6, 'L': 7, 'R': 8, 'T': 9, 'D': 10, 'A': 11, }
        letter_values = {Letter(letter): value for letter, value in solution.items()}
        # Evaluate each of the clues
        clue_values = {clue: clue.evaluators[0](letter_values) for clue in clue_list}
        solver = InnerSolver(clue_list, clue_values, letter_values)
        solver.solve(debug=False)

    def __init__(self, clue_list: Sequence[Clue], clue_values: KnownClueDict, letter_values: KnownLetterDict):
        super().__init__(clue_list)
        for clue in clue_list:
            clue.generator = self.generator
        self.clue_values = clue_values
        self.letter_values = letter_values

    def generator(self, clue: Clue) -> Sequence[str]:
        """
        Returns a list of all possible entry values for this clue.
        """
        value = self.clue_values[clue]  # The calculated value of this clue (as a string)
        value_length = len(value)
        expected_length = clue.length
        assert 1 <= expected_length - value_length <= 2
        if expected_length - value_length == 1:
            return [f'{value[:i]}{j}{value[i:]}'
                    for i, location in enumerate(clue.locations)
                    if self.is_intersection(location)
                    for j in range(1, 10)]
        else:
            return [f'{value[:i]}{j}{value[i:]}'
                    for i, location in enumerate(clue.locations)
                    for j in (10, 11)]

    def draw_grid(self, **args: Any) -> None:
        """
        Once we've solved the puzzle, we've overridden this function so that we print the graph with the shading
        that we want.
        """
        location_to_entry: Dict[Location, str] = args['location_to_entry']
        clue_values: Dict[Clue, ClueValue] = args['clue_values']

        shading = {}
        across_inserted_locations: Set[Location] = set()
        down_inserted_locations: Set[Location] = set()
        inserted_number: List[int] = []
        for clue in self._clue_list:
            original_clue_value = self.clue_values[clue]
            current_clue_value = clue_values[clue]
            delta = len(current_clue_value) - len(original_clue_value)
            start = len(commonprefix((original_clue_value, current_clue_value)))
            if clue.name == '32a':
                # Unfortunately, this clue ends with "111" and it's ambiguous which 11 is extra.  The final digit is an
                # extra part of 22d, so we have to use the earlier one.
                start -= 1
            assert original_clue_value == current_clue_value[:start] + current_clue_value[start + delta:]
            inserted_number.append(int(current_clue_value[start:start + delta]))
            locations = clue.locations[start:start + delta]
            (across_inserted_locations if clue.is_across else down_inserted_locations).update(locations)
            for location in locations:
                shading[location] = 'lightblue' if clue.is_across else 'pink'
        assert not across_inserted_locations.intersection(down_inserted_locations)

        # First, draw the grid with the extra acrosses and downs appropriately shaded
        super().draw_grid(shading=shading, **args)

        # Now, draw the grid with all 3's, 8's, and 9's highlighted in green
        shading = {location: 'lightgreen'
                   for location, entry in location_to_entry.items()
                   if entry in '389'}
        super().draw_grid(shading=shading, **args)

        # And just for fun, print the message
        value_to_letter_map = {value: letter for letter, value in self.letter_values.items()}
        message = ''.join(value_to_letter_map[i] for i in inserted_number)
        print(message)


if __name__ == '__main__':
    OuterSolver.run()
    # InnerSolver.test()
