import itertools
import re
from collections import Counter
from collections.abc import Hashable, Iterable, Sequence
from typing import Unpack, override

from more_itertools.more import map_reduce

from solver import (
    Clue,
    Clues,
    DancingLinksSolver,
    DLConstraint,
    DrawGridKwargs,
    EquationSolver,
    Evaluator,
    KnownClueDict,
    KnownLetterDict,
    Letter,
    Location,
)

CLUE_NUMBERS = False
PLOT_BOARD = True

ACROSS_LENGTHS = "3114/144/1113111/513/252/315/1113111/441/4113"
DOWN_LENGTHS = "243/1143/31311/333/414/333/11313/3411/342"

CLUES = """
1. A^(SS)
2. AS^S
3. NAG
4. BAN
5. E^S
6. E^S
7. N^(AN)
8. S^E-A
9. VIA
10. N^(AG)
11. N^(AG)+A
12. UR-N
13. AURA
14. UR+N
15. NUN
16. U^S
17. E^N
18. S^(AAB)
19. MIN-T
20. AUNE
21. BEE
22. V+EER
23. I^N
24. VIN+E
25. TENS-E
26. BUR+N
27. RUM+BA
28. NAVIG-ATE
29. (S^E-A)^S
30. G+RATIS
31. MISU-SE
32. (ABA)^S E^S
33. VE+RMIN
34. I+NSERT-SIGNS
35. RUM+U^N
36. BUST+RIBS
37. Unclued
38. TIGER+RUG
39. GERMAN+NAMIBIA
"""


def get_clues() -> tuple[Sequence[Clue], Sequence[Clue]]:
    clues = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
    new_clues = []
    equations = CLUES.strip().splitlines()
    lengths = sorted([clue.length for clue in clues])
    for index, (_length, equation) in enumerate(zip(lengths, equations, strict=True), start=1):
        match = re.fullmatch(r'(\d+)\. (.*)', equation)
        ix, info = match.groups()
        assert int(ix) == index
        if index != 37:
            base = (len(new_clues) + 1), 1
            new_clue = Clue(ix, True, base, 5)
            new_clue.evaluators = Evaluator.create_evaluators(info, wrapper=my_wrapper)
            new_clues.append(new_clue)
    return clues, new_clues


def my_wrapper(self, value_dict: dict[Letter, int]) -> Iterable[str]:
    try:
        result = self._compiled_code(*(value_dict[x] for x in self._vars))
        int_result = int(result)
        if result == int_result:
            if 0 <= int_result <= 99999:
                return str(int_result).rjust(5, '0'),
            else:
                return ()
        return ()
    except ArithmeticError:
        return ()


class Magpie285a(EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=False, max_debug_depth=100)

    def __init__(self) -> None:
        _, clues2 = get_clues()
        super().__init__(clues2, items=range(1, 13), allow_duplicates=True)
        self.add_constraints(clues2)

    def add_constraints(self, clues):
        for clue1, clue2 in itertools.combinations(clues, 2):
            self.add_constraint((clue1, clue2), lambda x, y: abs(int(x)) <= abs(int(y)))

    @override
    def get_allowed_regexp(self, location: Location) -> str:
        return '.'

    @override
    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict,
                      **more_args: Unpack[DrawGridKwargs],) -> None:
        self.show_letter_values(known_letters)
        results = [clue.evaluators[0].raw_call(known_letters) for clue in self.clue_list]
        print(results)


VALUES = [1, 4, 12, 21, 25, 25, 27, 31, 72, 81, 82, 85, 88, 91, 99,
          121, 125, 128, 152, 165, 175, 212, 216, 221, 295, 619, 799, 814, 961, 964,
          1178, 1225, 1356, 2118, 2123, 2212, 9952, 11124]


class Magpie285b(DancingLinksSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=True, max_debug_depth=100)

    def __init__(self) -> None:
        clues, _ = get_clues()
        super().__init__(clues)

    def update_constraints(self, constraints: dict[Hashable, list[DLConstraint]],
                           optional_constraints: set[str],
                           bounds: dict[str, tuple[int, int]]) -> None:
        # See how many times each clue number appears
        values_counter = Counter(str(x) for x in VALUES)
        # See which numbers are duplicates.  A duplicate can occur at most twice
        duplicates = {x for x in values_counter if values_counter[x] > 1}
        for duplicate in duplicates:
            assert values_counter[duplicate] == 2
        # Sort the values by length
        values_by_length = map_reduce(values_counter, lambda x: len(x))
        # Any square that occurs other than as the first square in a clue can't hold a minus
        minus_sign_illegal = {x for clue in self.clue_list for x in clue.locations[1:]}
        for clue in self.clue_list:
            # We have determined that the number of entries that must be entered negative is
            # precisely the same as the number of clues that can hold a negative number (i.e. its
            # first square is either an unch or the first square of another clue). So every clue
            # that can hold a negative number *must* hold a negative number
            is_positive = clue.location(0) in minus_sign_illegal
            value_length = clue.length - (not is_positive)
            clue_name = f'#{clue.name}'
            for value in values_by_length.get(value_length, ()):
                entry = value if is_positive else '-' + value
                constraints[clue, entry] = [
                    clue_name,
                    *clue.dancing_links_rc_constraints(entry),
                    # If value is a duplicate, we want exactly one of both value and -value
                    # if value is not a duplicate, we want exactly one of either value or -value.
                    f'Value-{entry if value in duplicate else value}',
                ]
            if value_length == 4:
                # Make sure name of constraint doesn't look like (clue, 'value')
                constraints[clue, None, None] = [clue_name, 'blank']

    @override
    def draw_grid(self, **args: Unpack[DrawGridKwargs]) -> None:
        if not PLOT_BOARD:
            return
        if not CLUE_NUMBERS:
            args['location_to_clue_numbers'].clear()
        if args['location_to_entry']:
            args['location_to_entry'][5, 5] = '0'
            args['shading'] = {(5, 5): 'red'}
            for key, item in args['location_to_entry'].items():
                if item == '-':
                    args['location_to_entry'][key] = '–'
        # clue_value = args['clue_values']
        # temp = [(clue.name, clue_value.get(clue, None)) for clue in self.clue_list]
        # print(temp)
        super().draw_grid(**args)


if __name__ == '__main__':
    Magpie285b.run()
