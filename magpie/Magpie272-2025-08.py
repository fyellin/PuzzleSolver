import itertools
from typing import Any, Optional

from solver import Clue, ClueValue, Clues, ConstraintSolver, generators
from solver.constraint_solver import AbstractLetterCountHandler

ACROSS_LENGTHS = "132/321/222/222/123/231"
DOWN_LENGTHS = "222/123/24/42/321/222"


class Magpie272(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.verify_is_180_symmetric()
        # solver.solve(start_clues=("4d", "11d"))
        solver.solve()

    def __init__(self) -> None:
        clues = Clues.clues_from_clue_sizes(ACROSS_LENGTHS, DOWN_LENGTHS)
        super().__init__(clues, letter_handler=MyLetterCountHandler())
        self.fixup_constraints()
        # self.extra_constraints()

    def fixup_constraints(self):
        for clue in self._clue_list:
            clue.generator = generators.allvalues

        for name in "2a 7a 9a 19a 20a 23a".split():
            self.clue_named(name).generator = generators.square

        self.add_constraint("5a 22a", lambda x, y: x == y[::-1])
        self.add_constraint("12a 14a", lambda x, y: x == y[::-1])
        self.add_constraint("10d 13d", lambda x, y: x == y[::-1])

        self.clue_named("11a").generator = generators.prime
        self.clue_named("16a").generator = generators.prime
        self.clue_named("3d").generator = generators.not_prime
        self.clue_named("20d").generator = generators.not_prime

        self.add_constraint("10a 17a", lambda x, y: (int(x) + int(y)) % 2 == 0)
        fibonacci = {21, 34, 55, 89, 144}
        self.add_constraint("1d 21d", lambda x, y: int(x) + int(y) in fibonacci)
        squares = {25, 36, 49, 64, 81, 100, 121, 144, 169, 196}
        self.add_constraint("6d 18d", lambda x, y: int(x) + int(y) in squares)

        self.add_constraint("5d 12a", lambda x, y: int(x) % int(y) == 0)
        self.add_constraint("15d 14a", lambda x, y: int(x) % int(y) == 0)

        self.clue_named("4d").generator = generators.triangular
        self.clue_named("11d").generator = generators.triangular

    def plot_board(self, clue_values: Optional[dict[Clue, ClueValue]] = None,
                   **more_args: Any) -> None:
        shading = {}
        for row, col in itertools.product(range(1, 7), repeat=2):
            if ((row - 1) // 2 + (col - 1) // 2) % 2:
                shading[(row, col)] = 'lightblue'
        super().plot_board(clue_values, shading=shading, **more_args)


class MyLetterCountHandler(AbstractLetterCountHandler):
    grid: list[int]
    magic_square: list[int]

    LOCATION_TO_OFFSET = {
        (row + 1, column + 1): qr * 12 + qc * 4 + rr * 2 + rc
        for row in range(6) for column in range(6)
        for qr, rr in [divmod(row, 2)]
        for qc, rc in [divmod(column, 2)]
    }

    EMPTY = -1000

    def start(self):
        self.grid = [self.EMPTY] * 36
        self.magic_square = [0] * 9
        # magic = np.array(((2, 9, 4), (7, 5, 3), (6, 1, 8)), dtype=int)
        # magics = [np.rot90(magic, i) for i in range(4)]
        # magics = magics + [x.T for x in magics]
        # self.all_magics = [m.reshape(9).tolist() for m in magics]

    def get_clue_info(self, clue: Clue):
        update_info = [(index, offset) for index, location in enumerate(clue.locations)
                       if self.grid[offset := self.LOCATION_TO_OFFSET[location]] < 0]
        return update_info

    ALL_MAGICS = ((2, 9, 4, 7, 5, 3, 6, 1, 8), (4, 3, 8, 9, 5, 1, 2, 7, 6),
                  (8, 1, 6, 3, 5, 7, 4, 9, 2), (6, 7, 2, 1, 5, 9, 8, 3, 4),
                  (2, 7, 6, 9, 5, 1, 4, 3, 8), (4, 9, 2, 3, 5, 7, 8, 1, 6),
                  (8, 3, 4, 1, 5, 9, 6, 7, 2), (6, 1, 8, 7, 5, 3, 2, 9, 4))

    def checking_value(self, value: ClueValue, info) -> bool:
        grid = self.grid
        self.adding_value(value, info)
        try:
            all_magics = self.ALL_MAGICS
            for index, (a, b, c, d) in enumerate(itertools.batched(grid, 4)):
                total = a + b + c + d
                if total >= 0:
                    total = (total % 9) or 9
                    all_magics = [x for x in all_magics if x[index] == total]
                    if not all_magics:
                        return False
            return True
        finally:
            self.removing_value(value, info)

    def adding_value(self, value: ClueValue, info: Any) -> None:
        for index, offset in info:
            self.grid[offset] = int(value[index])

    def removing_value(self, _value: ClueValue, info: Any) -> None:
        for _, offset in info:
            self.grid[offset] = self.EMPTY

    def close(self):
        assert all(value == self.EMPTY for value in self.grid)


if __name__ == '__main__':
    Magpie272.run()
