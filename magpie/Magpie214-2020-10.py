import math
from collections.abc import Sequence

from misc.factors import factor_sum, factor_count, shared_factor_count, odd_factor_count, even_factor_count
from solver import generators, ConstraintSolver, Clues, Clue
from solver.generators import filterer, allvalues

GRID = """
XX.XX
X.X..
XX.X.
XX.XX
X.X..
"""


class Solver214(ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Solver214()
        solver.verify_is_180_symmetric()
        solver.add_all_constraints()
        solver.solve(debug=True, max_debug_depth=50)
        # solver.solve()

    def __init__(self) -> None:
        super().__init__(self.get_clue_list())

    @staticmethod
    def get_clue_list() -> Sequence[Clue]:
        grid_locations = [(-1, -1)] + Clues.get_locations_from_grid(GRID)

        clues = [
            Clue("1a", True, grid_locations[1], 3, generator=filterer(lambda x: factor_count(x) == 6)),
            Clue("3a", True, grid_locations[3], 2, generator=allvalues),
            Clue("5a", True, grid_locations[5], 2, generator=filterer(lambda x: factor_count(factor_sum(x)) == 15)),
            Clue("6a", True, grid_locations[6], 3, generator=allvalues),
            Clue("8a", True, grid_locations[8], 3, generator=allvalues),
            Clue("10a", True, grid_locations[10], 3, generator=allvalues),
            Clue("12a", True, grid_locations[12], 2, generator=allvalues),
            Clue("14a", True, grid_locations[14], 2, generator=allvalues),
            Clue("15a", True, grid_locations[15], 3, generator=allvalues),

            Clue("1d", False, grid_locations[1], 2, generator=allvalues),
            Clue("2d", False, grid_locations[2], 3, generator=filterer(lambda x: factor_count(factor_sum(x)) == 16)),
            Clue("3d", False, grid_locations[3], 2, generator=allvalues),
            Clue("4d", False, grid_locations[4], 3, generator=allvalues),
            Clue("6d", False, grid_locations[6], 3, generator=allvalues),
            Clue("7d", False, grid_locations[7], 3, generator=generators.cube),
            Clue("9d", False, grid_locations[9], 3, generator=allvalues),
            Clue("11d", False, grid_locations[11], 2, generator=allvalues),
            Clue("13d", False, grid_locations[13], 2, generator=allvalues),
        ]
        return clues

    def add_all_constraints(self) -> None:
        self.add_constraint(("3a", "1a"), lambda x, y: factor_count(int(x)) > factor_count(int(y)))
        self.add_constraint(("8a", "6d"), lambda x, y: even_factor_count(int(x)) > even_factor_count(int(y)))
        self.add_constraint(("10a", "12a"), lambda x, y: factor_count(int(x)) > factor_count(int(y)))
        self.add_constraint(("12a", "1d"), lambda x, y: int(x) % int(y) == 0)
        self.add_constraint(("14a", "3a"), lambda x, y: factor_count(int(x)) == factor_count(int(y)))
        self.add_constraint(("15a", "2d"), lambda x, y: math.gcd(int(x), int(y)) > 1)
        self.add_constraint(("1d", "3d"), lambda x, y: factor_count(int(x)) > factor_count(int(y)))
        self.add_constraint(("4d", "13d"), lambda x, y: shared_factor_count(int(x), int(y)) > 5)
        # 6d will be handled in check_clue
        self.add_constraint(("13d", "3a"), lambda x, y: factor_count(int(x)) > factor_count(int(y)))

        self.add_constraint(("1a", "3a"), lambda x, y: even_factor_count(int(x)) == even_factor_count(int(y)))
        self.add_constraint(("5a", "6a"), lambda x, y: factor_sum(int(x)) == factor_sum(int(y)))
        self.add_constraint(("10a", "12a"), lambda x, y: odd_factor_count(int(x)) == odd_factor_count(int(y)))
        self.add_constraint(("14a", "15a"), lambda x, y: factor_count(int(x)) == factor_count(int(y)))

        self.add_constraint(("1d", "7d"), lambda x, y: even_factor_count(int(x)) == even_factor_count(int(y)))
        self.add_constraint(("2d", "11d"), lambda x, y: factor_sum(int(x)) == factor_sum(int(y)))
        self.add_constraint(("3d", "9d"), lambda x, y: odd_factor_count(int(x)) == odd_factor_count(int(y)))
        self.add_constraint(("4d", "13d"), lambda x, y: factor_count(int(x)) == factor_count(int(y)))

        six_down = self.clue_named("6d")
        for clue in self._clue_list:
            if clue != six_down:
                self.add_constraint((six_down, clue), lambda x, y: factor_count(int(x)) > factor_count(int(y)))



if __name__ == '__main__':
    temp = Solver214()
