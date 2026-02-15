import math
from typing import Any

from solver import Clue, ConstraintSolver, Evaluator, generators, Constraint, KnownClueDict

TRIANGLES = list(i * (i + 1) // 2 for i in range(2000))
SQUARES = list(i * i for i in range(1000))

TRIANGLES_SET = set(TRIANGLES)
SQUARES_SET = set(SQUARES)


TYPE1 = """
B, D, c 
B, d, h 
C, Dg, E 
J, L, k
Dg(H + j), K, h 
F(L – G), G(g – j), c –e
"""

TYPE2 = """
A – g, D, e/ F 
D, c, j– H 
G, H, f – G 
G + b/E, e – A, g – H 
a, F + e, g
"""

VALUES = dict(A=37, B=2079, C=324, D=27, E=20, F=21, G=45, H=11, J=594, K=2277, L=54,
              a=33, b=720, c=77, d=945, e=42, f=252, g=15, h=495, j=12, k=44)

CLUES = [
    ('A', 1, 1, 2),
    ('B', 1, 3, 4),
    ('C', 2, 1, 3),
    ('D', 2, 4, 2),
    ('E', 3, 1, 2),
    ('F', 3, 3, 2),
    ('G', 3, 5, 2),
    ('H', 4, 2, 2),
    ('J', 4, 4, 3),
    ('K', 5, 1, 4),
    ('L', 5, 5, 2),

    ('a', 1, 1, 2),
    ('b', 1, 2, 3),
    ('c', 1, 5, 2),
    ('d', 1, 6, 3),
    ('e', 2, 3, 2),
    ('f', 3, 1, 3),
    ('g', 3, 4, 2),
    ('h', 3, 5, 3),
    ('j', 4, 2, 2),
    ('k', 4, 6, 2)
]


class Magpie243(ConstraintSolver):
    @staticmethod
    def run():
        solver = Magpie243()
        solver.verify_is_180_symmetric()
        # result = {solver.clue_named(name): str(value) for name, value in VALUES.items()}
        # solver.plot_board(result)
        solver.solve(debug=False)

    def __init__(self):
        allvalues = generators.allvalues
        clues = [Clue(name, name.isupper(), (r, c), length, generator=allvalues)
                 for name, r, c, length in CLUES]
        constraints = self.get_constraints()
        super().__init__(clues, constraints)
        self.get_constraints()

    def show_solution(self, known_clues: KnownClueDict) -> None:
        type1, type2 = self.grab_constraints()
        def show(type, count, a, b, c):
            if type == 1:
                print(f'{a:4} {b:4} {c:4} || '
                      f'{math.isqrt(a * b//c):3} {math.isqrt(a * c // b):3} {math.isqrt(b * c // a):3}')
            else:
                print(f'{a:4} {b:4} {c:4}')
            return 0
        mapping = dict(show=show)
        vars = {clue.name: int(value) for clue, value in known_clues.items()}
        for i, constraint in enumerate(type1):
            evaluator = Evaluator.create_evaluator(f'@show(1, {i}, {constraint})', mapping)
            evaluator(vars)
        for i, constraint in enumerate(type2):
            evaluator = Evaluator.create_evaluator(f'@show(2, {i}, {constraint})', mapping)
            evaluator(vars)
        super().show_solution(known_clues)

    def draw_grid(self, location_to_clue_numbers, **args: Any) -> None:
        for location, clues in location_to_clue_numbers.items():
            if len(clues) == 1 and clues[0].islower():
                clues.insert(0, '')
        shading = {(5, c): 'lightgreen' for c in range(2, 6)}
        super().draw_grid(location_to_clue_numbers=location_to_clue_numbers,
                          shading=shading, **args)

    @staticmethod
    def is_type_1_triple(a, b, c):
        if a <= 0 or b <= 0 or c <= 0:
            return False
        for x, y, z in ((a, b, c), (b, c, a), (a, c, b)):
            q, r = divmod(x * y, z)
            if r != 0 or q not in SQUARES_SET:
                return False
        return True

    @staticmethod
    def is_type_2_triple(a, b, c):
        return {a * b + 1, b * c + 1, a * c + 1} <= TRIANGLES_SET

    @staticmethod
    def grab_constraints():
        return tuple([line for line in constraints.splitlines() if line]
                     for constraints in (TYPE1, TYPE2))

    @classmethod
    def get_constraints(cls) -> list[Constraint]:
        result = []
        mapping = dict(test1=cls.is_type_1_triple, test2=cls.is_type_2_triple,
                       testx=lambda x: x + 1 in TRIANGLES_SET,
                       testnz=lambda x: int(x) == x > 0)
        type1, type2 = cls.grab_constraints()
        for c_type, constraints in ((1, type1), (2, type2)):
            for constraint in constraints:
                evaluator = Evaluator.create_evaluator(f'@test{c_type}({constraint})', mapping)
                result.append(cls.evaluator_to_constraint(evaluator))
                pieces = constraint.split(',')
                assert len(pieces) == 3
                for piece in pieces:
                    if c_type == 1:
                        evaluator = Evaluator.create_evaluator(f'@testx({piece})', mapping)
                    elif len(piece.strip()) > 1:
                        evaluator = Evaluator.create_evaluator(f'@testnz({piece})', mapping)
                    else:
                        continue
                    result.append(cls.evaluator_to_constraint(evaluator))

        return result

    @classmethod
    def evaluator_to_constraint(cls, evaluator) -> Constraint:
        code_vars = evaluator.vars
        return Constraint(code_vars,
                          lambda *v: evaluator.compiled_code(*[int(x) for x in v]))

if __name__ == '__main__':
    Magpie243.run()
