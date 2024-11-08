import ast
import itertools
from collections import defaultdict

from solver import Clue, Clues, ConstraintSolver, DancingLinks, Encoder
from solver.constraint_solver import Constraint
from solver.equation_parser import EquationParser
from solver.equation_solver import KnownClueDict
from solver.generators import known, prime_generator

LINES = """
A triangular
B prime
D prime
F multiple of A
G triangular, multiple of A
J multiple of A
K multiple of B
L triangular
N prime
O multiple of B and C
P triangular, multiple of E 
Q multiple of A and G
R multiple of A, E and G 
S multiple of B
U multiple of D
V multiple of A
Y multiple of A, B, C and O 
CC prime
EE multiple of A and F
T D
W M –K
X G– D – D
Z A+ F
AA L –D –I
BB N – A– L 
DD C+ F
FF H –C
GG U + F – A –T 
HH E+ F + F
"""


def upto(iterator):
    return itertools.takewhile(lambda x: x < 100_000, iterator)


PRIMES = {str(x) for x in upto(prime_generator())}
TRIANGLES = {str(x) for x in upto(i * (i + 1) // 2 for i in itertools.count(1))}
VALUES = list(upto(x for i in itertools.count(1) for j in [i * i] for x in (j - 1, j + 1)))

CLUE_LETTERS = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ") + [f'{x}{x}' for x in 'ABCDEFGH']


def parse_line_input():
    primes = []
    triangles = []
    multiples = []
    squares = []
    lines = LINES.strip().splitlines()
    for line in lines[0:-10]:
        line = line.strip()
        if not line:
            continue
        letter, stuff = line.split(' ', maxsplit=1)
        if 'triangular' in line:
            triangles.append(letter)
        if 'prime' in line:
            primes.append(letter)
        if 'multiple of' in line:
            index = line.index('multiple of ')
            line = line[index + 12:].replace(' and ', ', ')
            for divisor in line.split(', '):
                multiples.append((divisor, letter))
    for line in lines[-10:]:
        letter, expression = line.split(' ', maxsplit=1)
        squares.append((letter, expression))
    return primes, triangles, multiples, squares


class Magpie263 (ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=True)
        solver.verify()
        result = [(clue.name, solver.output[clue.name]) for clue in solver._clue_list]
        Magpie263b.run(result)

    def __init__(self) -> None:
        primes, triangles, multiples, squares = parse_line_input()
        clues = self.get_clues()
        self.constraints = self.get_constraints_from_clues(clues, primes, triangles, multiples, squares)
        super().__init__(clues, constraints=self.constraints)
        self.output = defaultdict(set)

    def get_clues(self):
        return [
            Clue(letter, True, (i, 1), length, generator=known(*VALUES))
            for i, letter in enumerate(CLUE_LETTERS, start=1)
            for length in [2 if i <= 6 else 3 if i <= 18 else 4 if i <= 32 else 5]
        ]

    def get_constraints_from_clues(self, clues, primes, triangles, multiples, squares):
        equation_parser = EquationParser()
        constraints = []

        def match(letter, expression):
            return abs(letter - expression ** 2) == 1

        def is_prime(x): return x in PRIMES
        def is_not_prime(x): return x not in PRIMES
        def is_triangle(x): return x in TRIANGLES
        def is_not_triangle(x): return x not in TRIANGLES
        for clue in clues:
            constraints.append(Constraint((clue,), is_prime if clue.name in primes else is_not_prime))
            constraints.append(Constraint((clue,), is_triangle if clue.name in triangles else is_not_triangle))

        def less_than(x, y): return x < y
        def is_multiple(x, y): return int(y) % int(x) == 0
        def is_not_multiple(x, y): return int(y) % int(x) != 0
        for clue1, clue2 in itertools.combinations(clues, 2):
            name1, name2 = clue1.name, clue2.name
            if clue1.length == clue2.length:
                constraints.append(Constraint((clue1, clue2), less_than, name=f'{name1}<{name2}'))
            if (clue1.name, clue2.name) in multiples:
                constraints.append(Constraint((clue1, clue2), is_multiple, name=f'{name1}|{name2}'))
            else:
                constraints.append(Constraint((clue1, clue2), is_not_multiple, name=f'{name1}\u2224{name2}'))

        for letter, expression in squares:
            parsed = equation_parser.parse(f'@match(${letter}, {expression})')[0]
            parsed_vars = parsed.vars()
            # expression here will be a lambda expression, such as lambda x, y: x + y
            expression = ast.unparse(parsed.get_ast_expression(()))
            # "lambda x, y: (lambda x, y: x + y)(int(x), int(y))"
            expression = f'lambda {', '.join(parsed_vars)}: ({expression})({', '.join(f'int({x})' for x in parsed_vars)})'
            compiled_code = eval(expression, {'match': match}, None)
            constraints.append(Constraint(parsed_vars, compiled_code, letter))
        return constraints

    def show_solution(self, known_clues: KnownClueDict) -> None:
        for clue, value in known_clues.items():
            self.output[clue.name].add(int(value))

    def verify(self):
        output = self.output
        for values in output.values():
            assert all(value in VALUES for value in values)
        for used_vars, evaluator, name in self.constraints:
            my_list = [output[letter] for letter in used_vars]
            for values in itertools.product(*my_list):
                assert evaluator(*values)


SOLUTION = (
    ('A', {10}), ('B', {17}), ('C', {26}), ('D', {37}), ('E', {48}),
    ('F', {50}), ('G', {120}), ('H', {122}), ('I', {226}), ('J', {290}),
    ('K', {323}), ('L', {325}), ('M', {362}), ('N', {401}), ('O', {442}),
    ('P', {528}), ('Q', {840}), ('R', {960}), ('S', {1088, 1224}), ('T', {1368}),
    ('U', {1443}), ('V', {1520}), ('W', {1522}), ('X', {2115, 2117}), ('Y', {2210}),
    ('Z', {3601, 3599}), ('AA', {3843, 3845}), ('BB', {4355}), ('CC', {4357, 5477}),
    ('DD', {5777, 5775}), ('EE', {8650}), ('FF', {9217, 9215}), ('GG', {13224}),
    ('HH', {21905, 21903}))


class Magpie263b(ConstraintSolver):
    @classmethod
    def run(cls, solution=None):
        solver = cls(solution)
        solver.my_solve()

    def __init__(self, solution):
        self.solution = solution or SOLUTION
        clues = self.get_clues()
        super().__init__(clues)

    def my_solve(self):
        solution = self.dancing_links()
        clue_values = {self.clue_named(name): value for name, value in solution}
        print(clue_values)
        self.plot_board(clue_values)

    def dancing_links(self):
        encoder = Encoder.digits()
        constraints = {}
        for clue in self._clue_list:
            for xletter, values in self.solution:
                for value in (str(x) for x in values):
                    if clue.length == len(value):
                        constraint = [f'{clue.name}', f'{xletter}']
                        for location, letter in zip(clue.locations, value, strict=True):
                            if self.is_intersection(location):
                                constraint.extend(
                                    encoder.encode(letter, location, clue.is_across))
                        constraints[(clue.name, value)] = constraint
        solutions = []
        solver = DancingLinks(constraints, row_printer=lambda x: solutions.append(x))
        solver.solve()
        solution, = solutions
        return solution

    ACROSS = "44/341/1124/332/233/4211/143/44"
    DOWN = "314/152/44/3311/1133/44/251/413"

    def get_clues(self):
        return Clues.grid_from_clue_sizes(self.ACROSS, self.DOWN)


if __name__ == '__main__':
    Magpie263.run()
