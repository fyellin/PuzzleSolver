import itertools
import re
from collections.abc import Iterable, Sequence

from solver import (
    Clue,
    Clues,
    EquationSolver,
    Evaluator,
)
from solver.helpers import is_square

ACROSS = "3131/11312/3311/1331/1133/21311/1313"
DOWN = "223/133/313/3211/1123/313/331/322"


CLUES = """
Set 1
1ac K − I (3)
12ac O = ss − K − uu (3)
23ac L + Y + y − a (3)
1dn n + s − G (2)
Set 2
10ac S − o − o − W (2)
24ac B + B + B (2)
15dn B + s + y (2)
26dn L − a − B (2)
Set 3
21ac ss + uu (3)
2dn C + N + N (3)
17dn N + P + u (3)
23dn I + u + u + w (3)
Set 4
5dn D + S − n − n (3)
6dn e + R − i − n (3)
11dn t − K − L (2)
21dn ss + w (3)
Set 5
8dn r − B − T (3)
18dn U + u − c − t (2)
20dn c + c + T − E (3)
22dn Y − u − u (3)
Set 6
11ac U + y − l − n (3)
16ac N − u (3)
28ac a + H − L − Y (3)
3dn A + A − e − w (3)
Set 7
4ac O + W − n (3)
9ac E − A − c − w (3)
7dn Unclued (3)
13dn s − B (2)
Set 8
14ac B + r + T − c (3)
25ac n + U − r − t (3)
27ac I + r − N − t (3)
19dn Unclued (3)
"""


class Listener4922 (EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=True, max_debug_depth=100)

    def __init__(self):
        self.clues = clues = Clues.clues_from_clue_sizes(ACROSS, DOWN)
        self.square_sets = []
        self.read_clue_definitions(clues)
        super().__init__(clues, items=[x * x for x in range(2, 51)])
        for a, b, c, d in self.square_sets:
            self.add_constraint((a, b, c, d), lambda a, b, c, d: is_square(int(a) + int(b) + int(c) + int(d)))
            # self.add_constraint((a, b, c, d), self.cubism)

    def cubism(self, a, b, c, d):
        a, b, c, d = int(a) ** 3, int(b) ** 3, int(c) ** 3, int(d) ** 3
        return a + b == c + d or a + c == b + d or a + d == b + c

    def read_clue_definitions(self, clues: Sequence[Clue]):
        clue_by_name = {clue.name: clue for clue in clues}
        clues_in_order = []
        for line in CLUES.strip().splitlines():
            if line.startswith("Set"):
                continue
            match = re.match(r"(\d+)(dn|ac) (.*) \((\d)\)", line)
            number, is_across, expression, length = match.groups()
            clue = clue_by_name[number + is_across[0]]
            assert int(length) == clue.length
            if "Unclued" not in expression:
                clue.expression = expression
                clue.evaluators = Evaluator.create_evaluators(expression)
            clues_in_order.append(clue)
        self.square_sets = list(itertools.batched(clues_in_order, 4))  # noqa: B911


if __name__ == '__main__':
    Listener4922.run()
