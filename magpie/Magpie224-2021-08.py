import itertools
import math
from collections.abc import Sequence, Iterable

from solver import Clue, ConstraintSolver, generators, Location, ClueValue
from solver.constraint_solver import Constraint, KnownClueDict


def digit_sum(value: ClueValue) -> int:
    return sum(int(x) for x in str(value))


def digit_product(value: ClueValue) -> int:
    return math.prod(int(x) for x in str(value))

def triangular_permutation(clue: Clue):
    for value in generators.triangular(clue):
        for digits in itertools.permutations(str(value)):
            if digits[0] != '0' and ''.join(digits) != str(value):
                yield ''.join(digits)

def non_decreasing(clue: Clue) -> Iterable[str]:
    for digits in itertools.combinations_with_replacement('123456789', clue.length):
        yield ''.join(digits)


CLUE_INFO = [
    ('ba', 36, 37, 1),
    ('ce', 5, 39, 38),
    ('db', 4, 37, 36),
    ('dj', 4, 7, 10),
    ('dk', 4, 6, 7, 44),   # special
    ('ec', 38, 39, 5),
    ('if', 9, 42, 40),
    ('jg', 10, 43, 41),
    ('kl', 44, 15, 48),
    ('ln', 48, 22, 49),
    ('mh', 46, 12, 8),
    ('pm', 24, 18, 46),
    ('ps', 24, 54, 53),
    ('pu', 24, 54, 31),
    ('pv', 24, 27, 57),
    ('qo', 51, 20, 21),
    ('rw', 52, 29, 58),
    ('xy', 59, 33, 60),
    ('yz', 60, 58, 34),
    ('hm', 8, 12, 46),
    ('bd', 36, 37, 4),
    ('zt', 34, 35, 56),
    ('vu', 57, 32, 31),
]

GENERATORS = {
    'ce': generators.not_prime,
    'db': generators.prime,
    'dj': generators.square,
    'if': triangular_permutation,
    'jg': generators.triangular,
    'kl': generators.prime,
    'ln': generators.prime,
    'ps': generators.prime,
    'rw': generators.prime,
    'xy': non_decreasing,
}

VERTICES = [
    (1, 2, 37, 4, 38),
    (1, 36, 37),
    (2, 38, 39),
    (3, 36, 37, 6, 9, 42, 40),
    (37, 6, 4),
    (4, 7, 38),
    (38, 39, 5, 41, 43, 10, 7),
    (8, 40, 42),
    (41, 43, 11),
    (8, 42, 13, 46, 12),
    (42, 13, 9),
    (9, 6, 44, 14, 47),
    (7, 10, 48, 15, 44),
    (10, 43, 16),
    (11, 17, 49, 16, 43),
    (12, 45, 46),
    (46, 13, 18),
    (14, 15, 19, 20, 21),
    (16, 22, 49),
    (17, 49, 50),
    (23, 45, 46, 18, 24, 54, 53),
    (18, 47, 19, 51, 24),
    (53, 54, 31),
    (24, 54, 27),
    (22, 49, 50, 26, 56, 55, 25),
    (20, 52, 29, 28, 51),
    (55, 56, 35),
    (31, 54, 27, 57, 32),
    (27, 28, 57),
    (32, 57, 59),
    (28, 29, 58, 60, 33, 59, 57),
    (29, 30, 58),
    (58, 60, 34),
    (30, 55, 35, 34, 58),
    (25, 30, 55),
    (48, 22, 25, 52, 21)
]


class Magpie224 (ConstraintSolver):
    real_start_locations: set[Location]

    @staticmethod
    def run():
        solver = Magpie224()
        solver.solve(debug=False, max_debug_depth=200)

    def __init__(self) -> None:
        clues = self.get_clues()
        constraints = self.get_constraints()
        self.real_start_locations = {(loc0, 1) for _name, loc0, *_loc in CLUE_INFO}
        super().__init__(clues, constraints=constraints)

    @staticmethod
    def get_clues() -> Sequence[Clue]:
        def build_clue(name: str, *vertices: int) -> Clue:
            squares = tuple((x, 1) for x in vertices)
            generator = GENERATORS.get(name, generators.allvalues)
            return Clue(name, True, squares[0], len(squares), locations=squares, generator=generator)

        clues = [
            *[Clue(f'{i}', True, (i, 1), 1, generator=lambda _: range(10)) for i in range(1, 61)],
            *[build_clue(*args) for args in CLUE_INFO]
        ]
        return clues

    def get_constraints(self) -> Sequence[Constraint]:
        l_and_friends = ('10', '7', '43', '16', '48')

        def check_vertex(*values: str) -> bool:
            return sum(int(value) for value in values) % len(values) == 0

        return [
            Constraint(("ba", "ec"), lambda ba, ec: int(ba) < int(ec)),
            Constraint(('ec', 'xy'), lambda ec, xy: int(ec) % digit_sum(xy) == 0),
            Constraint(('ln', 'hm'), lambda ln, hm: digit_product(ln) < digit_product(hm)),
            Constraint(('mh', 'zt'), lambda mh, zt: digit_sum(mh) == digit_sum(zt)),
            Constraint(('pm', 'pv'), lambda pm, pv: int(pm) > int(pv)),
            Constraint(('pu', 'zt'), lambda pu, zt: digit_product(pu) == digit_product(zt)),
            Constraint(('pv', 'bd'), lambda pv, bd: int(bd) % int(pv) == 0 and int(bd) > int(pv)),
            Constraint(('qo', 'vu'), lambda qo, vu: int(vu) % int(qo) == 0 and int(vu) > int(qo)),
            *[
                Constraint(tuple(str(vertex) for vertex in vertices), check_vertex,
                           name=','.join(str(vertex) for vertex in vertices))
                for vertices in VERTICES
            ],
            Constraint(('yz', *l_and_friends), lambda a, *b: int(a) == math.prod(int(x) for x in b), name="JJJ"),
            # These aren't really necessary, but they speed up the program just a tad.
            # Any subset of the multipliers must be a divisor of yz.
            *[
                Constraint(('yz', *vertices), lambda a, *b: int(a) % math.prod(int(x) for x in b) == 0)
                for count in range(1, 5)
                for vertices in itertools.combinations(l_and_friends, count)
            ],
            Constraint(('dk',), lambda value: value[0] <= value[1] <= value[3] or value[0] <= value[2] <= value[3]),
        ]

    def show_solution(self, known_clues: KnownClueDict) -> None:
        items = [(clue.name, known_clues[clue]) for clue in self._clue_list]
        print(', '.join(f'{name}:{value}' for name, value in items))

    def add_all_constraints(self) -> None:
        pass


    def get_allowed_regexp(self, location: Location) -> str:
        loc = location[0]
        if loc > 35:
            return '[13579]'
        elif location in self.real_start_locations:
            return '[2468]'
        else:
            return '[02468]'


if __name__ == '__main__':
    Magpie224.run()
