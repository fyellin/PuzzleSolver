import itertools
from typing import Sequence, List, Set, Iterator, Callable, Union, Dict, Any

from solver import Clue, ConstraintSolver, ClueValue, Location, ClueValueGenerator
from solver import generators
from solver.constraint_solver import KnownClueDict

squares = set(itertools.takewhile(lambda x: x < 1000, (x**2 for x in itertools.count())))
triangles = set(itertools.takewhile(lambda x: x < 1000, (x * (x + 1) // 2 for x in itertools.count())))


def digit_sum(value: Union[int, str]) -> int:
    return sum(int(x) for x in str(value))


def is_square(x: int) -> bool:
    return x in squares


def is_triangular(x: int) -> bool:
    return x in triangles


def is_fibonacci(x: int) -> bool:
    assert x < 100
    return x in (1, 2, 3, 5, 8, 13, 21, 34, 55, 89)



class Solver210(ConstraintSolver):
    solutions: List[KnownClueDict]

    @staticmethod
    def run() -> None:
        exclusions: Set[int] = set()
        solver1 = Solver210('a', exclusions)
        solver1.solve()
        exclusions.update(int(x) for x in solver1.solutions[0].values())
        print([(clue.name, value) for clue, value in solver1.solutions[0].items()])

        solver2 = Solver210('b', exclusions)
        solver2.solve()
        exclusions.update(int(x) for x in solver2.solutions[0].values())
        print([(clue.name, value) for clue, value in solver2.solutions[0].items()])

        solver3 = Solver210('cd', exclusions)
        solver3.solve()
        print([(clue.name, value) for clue, value in solver3.solutions[0].items()])

    @staticmethod
    def foobar() -> None:
        solver = Solver210('abcd', set())
        answers = [
            ('14dA', '37'), ('9aA', '47'), ('13aA', '23'), ('9dA', '425'), ('10aA', '245'), ('16aA', '957'),
            ('5dA', '197'), ('12dA', '59'), ('11dA', '43'), ('3dA', '35'), ('15aA', '13'), ('8dA', '121'),
            ('8aA', '11'), ('4aA', '91'), ('4dA', '97'), ('7aA', '579'), ('1aA', '133'), ('1dA', '15'), ('6aA', '55'),
            ('2dA', '351'),
            ('14dB', '26'), ('9aB', '32'), ('13aB', '72'), ('9dB', '378'), ('10aB', '738'), ('16aB', '486'),
            ('5dB', '882'), ('12dB', '84'), ('11dB', '36'), ('3dB', '44'), ('15aB', '66'), ('8dB', '676'),
            ('8aB', '62'), ('4aB', '18'), ('4dB', '16'), ('7aB', '468'), ('1aB', '644'), ('1dB', '64'), ('6aB', '46'),
            ('2dB', '462'),
            ('14dD', '48'), ('14dC', '51'), ('13aC', '25'), ('13aD', '94'), ('9aD', '30'), ('9dD', '394'),
            ('10aC', '439'), ('5dD', '820'), ('16aD', '848'), ('11dC', '39'), ('12dC', '93'), ('3dD', '42'),
            ('12dD', '68'), ('15aC', '19'), ('4aD', '58'), ('4dD', '50'), ('7aD', '202'), ('4dC', '87'), ('7aC', '575'),
            ('4aC', '89'), ('5dC', '953'), ('10aD', '926'), ('16aC', '391'), ('9dC', '629'), ('9aC', '63'),
            ('11dD', '20'), ('3dC', '75'), ('8dC', '441'), ('8aD', '12'), ('8aC', '41'), ('8dD', '196'), ('15aD', '60'),
            ('1aD', '574'), ('1dD', '54'), ('6aD', '40'), ('2dC', '291'), ('1aC', '427'), ('2dD', '702'), ('1dC', '49'),
            ('6aC', '99')]
        known_clues = {solver.clue_named(name): ClueValue(value) for (name, value) in answers}
        solver.plot_board(known_clues)

    def __init__(self, which: str, exclusions: Set[int]) -> None:
        clue_list = self.make_clue_list(which, exclusions)
        super(Solver210, self).__init__(clue_list)
        self.add_constraints(which)
        self.solutions = []

    def add_constraints(self, which: str) -> None:
        self.add_my_constraint(which, ("7a", "4d"), lambda a7, d4: is_square(int(a7) + int(d4)))
        self.add_my_constraint(which, ("9a", "14d"), lambda a9, d14: is_triangular(abs(int(a9) - int(d14))))
        self.add_my_constraint(which, ("10a", "9d"), lambda a10, d9: sorted(a10) == sorted(d9))
        self.add_my_constraint(which, ("16a", "10a"), lambda a16, a10: int(a16) % digit_sum(a10) == 0)

        self.add_my_constraint(which, ("2d", "6a", "8a", "1d"),
                               lambda d2, a6, a8, d1: int(d2) ==  3 * (int(a6) + int(a8) + int(d1[::-1])))
        self.add_my_constraint(which, ("5d", "10a"),
                               lambda d5, a10: int(d5) == sum(int(x)**3 for x in a10))
        self.add_my_constraint(which, ("8d", "8a"), lambda d11, a8: int(d11) == int(a8[::-1]) ** 2)
        self.add_my_constraint(which, ("11d", "3d"), lambda d11, d3: is_fibonacci(abs(int(d3) - int(d11))))


    def add_my_constraint(self, which: str, vars: Sequence[str], predicate: Callable[..., bool]) -> None:
        if 'a' in which:
            vars_for_a = [var + "A" for var in vars]
            self.add_constraint(vars_for_a, predicate)

        if 'b' in which:
            vars_for_b = [var + "B" for var in vars]
            self.add_constraint(vars_for_b, predicate)

        first, *rest = vars
        if 'c' in which:
            vars_for_c = [first + "C"] + [var + "D" for var in rest]
            self.add_constraint(vars_for_c, predicate)

        if 'd' in which:
            vars_for_d = [first + "D"] + [var + "C" for var in rest]
            self.add_constraint(vars_for_d, predicate)

    def make_clue_list(self, which: str, exclusions: Set[int]) -> List[Clue]:
        temp = (
            (1,  True, (1, 1), 3, tuple(range(7, 1000, 7))),
            (4,  True, (1, 4), 2, None),
            (6,  True, (2, 1), 2, None),
            (7,  True, (2, 3), 3, None),
            (8,  True, (3, 1), 2, None),
            (9,  True, (3, 4), 2, None),
            (10, True, (4, 1), 3, None),
            (13, True, (4, 4), 2, None),
            (15, True, (5, 1), 2, None),
            (16, True, (5, 3), 3, None),

            (1, False, (1, 1), 2, None),
            (2, False, (1, 2), 3, None),
            (3, False, (1, 3), 2, None),
            (4, False, (1, 4), 2, None),
            (5, False, (1, 5), 3, None),
            (8, False, (3, 1), 3, None),
            (9, False, (3, 4), 3, None),
            (11, False, (4, 2), 2, None),
            (12, False, (4, 3), 2, None),
            (14, False, (4, 5), 2, (15, 26, 37, 48, 59, 40, 51, 62, 73, 84, 95)),
        )
        clue_list = []
        for (number, is_across, (row, column), length, values) in temp:
            generator = generators.known(*values) if values else generators.allvalues

            def parity_generator(generator:ClueValueGenerator, parity: int) -> ClueValueGenerator:
                def new_generator(clue: Clue) -> Iterator[Union[int, str]]:
                    for x in generator(clue):
                        if int(x) % 2 == parity and int(x) not in exclusions:
                            yield x
                return new_generator

            even_generator = parity_generator(generator, 0)
            odd_generator = parity_generator(generator, 1)


            name = str(number) + ('a' if is_across else 'd')
            if 'a' in which:
                clue_list.append(Clue(name + 'A', is_across, (row, column), length, generator=odd_generator))
            if 'b' in which:
                clue_list.append(Clue(name + 'B', is_across, (row, column + 6), length, generator=even_generator))
            if 'c' in which:
                clue_list.append(Clue(name + 'C', is_across, (row + 6, column), length, generator=odd_generator))
            if 'd' in which:
                clue_list.append(Clue(name + 'D', is_across, (row + 6, column + 6), length, generator=even_generator))
        return clue_list

    def show_solution(self, known_clues: KnownClueDict) -> None:
        self.solutions.append(known_clues.copy())
        super().show_solution(known_clues)

    def draw_grid(self, **args: Any) -> None:
        location_to_entry: Dict[Location, str] = args['location_to_entry']
        location_to_entry[3,3] = 'A'
        location_to_entry[3,9] = 'B'
        location_to_entry[9,3] = 'C'
        location_to_entry[9,9] = 'D'  #c9b9db
        shading = {(row, column) : '#c9b9db' for row in (3, 9) for column in (3, 9)}
        super().draw_grid(shading=shading, **args)


if __name__ == '__main__':
    Solver210.foobar()
