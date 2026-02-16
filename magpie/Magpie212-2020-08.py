import itertools
from collections.abc import Sequence, Iterable

from solver import Clue, ConstraintSolver, ClueValueGenerator, KnownClueDict
from solver import generators


class Solver212(ConstraintSolver):
    solutions: list[KnownClueDict]

    def __init__(self, clue_list: Sequence[Clue]) -> None:
        super().__init__(clue_list)
        self.add_constraint(('16a', '12d'), lambda m, d: int(m) % int(d) == 0)
        self.add_constraint(('21a', '1d'), lambda d, m: int(m) % int(d) == 0)
        self.add_constraint(('1d', '6d'), lambda m, d: int(m) % int(d) == 0)
        self.add_constraint(('3d', '4d'), lambda m, d: int(m) % int(d) == 0)
        self.add_constraint(('17d', '23a'), lambda m, d: int(m) % int(d) == 0)
        self.add_constraint(('19d', '13d', '18a'), lambda s, a1, a2: int(s) == int(a1) + int(a2))
        # self.add_constraints(which)

    @staticmethod
    def run() -> None:
        clue_list = Solver212.get_clue_list()
        for clue in clue_list:
            clue.generator = Solver212.get_generator(clue)
        solver = Solver212(clue_list)
        solver.solve(debug=True)

    @staticmethod
    def get_clue_list() -> Sequence[Clue]:
        possibilities = ((3, 3), (2, 2, 2), (1, 2, 3), (1, 3, 2), (3, 1, 2), (3, 2, 1), (2, 1, 3), (2, 3, 1),
                         (1, 2, 1, 2), (2, 1, 2, 1), (1, 2, 2, 1))
        for rows in itertools.product(possibilities, repeat=3):
            acrosses: dict[tuple[int, int], int] = {}
            downs: dict[tuple[int, int], int] = {}
            for row, lengths in enumerate(rows, start=1):
                column = 1
                for length in lengths:
                    if length != 1:
                        acrosses[row, column] = length
                        downs[column, 7 - row] = length
                        acrosses[7 - row, 7 - column - (length - 1)] = length
                        downs[7 - column - (length - 1), row] = length
                    column += length
                assert column == 7
            number_to_clue_start = Solver212.verify_is_legal_grid(acrosses, downs)
            if number_to_clue_start:
                result = []
                for number, clue_start in number_to_clue_start.items():
                    if clue_start in acrosses:
                        result.append(Clue(f'{number}a', True, clue_start, acrosses[clue_start]))
                    if clue_start in downs:
                        result.append(Clue(f'{number}d', False, clue_start, downs[clue_start]))
                return result
        return ()

    @staticmethod
    def verify_is_legal_grid(acrosses: dict[tuple[int, int], int], downs: dict[tuple[int, int], int]) \
            -> dict[int, tuple[int, int]] | None:
        clue_starts = set(acrosses.keys()).union(downs.keys())
        number_to_clue_start = {number: clue_start for number, clue_start in enumerate(sorted(clue_starts), start=1)}
        for number, clue_start in number_to_clue_start.items():
            value = (clue_start in acrosses) + (clue_start in downs)
            assert 1 <= value <= 2
            expected_value = 2 if number in (2, 3, 6, 16, 21) else 1
            if value != expected_value:
                return None
        return number_to_clue_start

    @staticmethod
    def get_generator(clue: Clue) -> ClueValueGenerator:
        base_generator: ClueValueGenerator
        if clue.name == '5a':
            base_generator = generators.prime
        elif clue.name == '14a' or clue.name == '8d':
            base_generator = generators.square
        elif clue.name == '15d':
            base_generator = generators.not_prime
        else:
            base_generator = generators.allvalues

        def result(clue: Clue) -> Iterable[str | int]:
            for value in base_generator(clue):
                split = list(str(value))
                if clue.is_across:
                    if all(x < y for x, y in zip(split, split[1:])):
                        yield value
                else:
                    if all(x > y for x, y in zip(split, split[1:])):
                        yield value

        return result


if __name__ == '__main__':
    Solver212.run()

