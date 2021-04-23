import itertools
import os
import pickle
from functools import lru_cache
from typing import Dict, Sequence, Iterable, Tuple, Set, ClassVar

from cell import House
from features import PossibilitiesFeature
from human_sudoku import Sudoku
from misc.factors import divisor_count, prime_factors, factor_count


class PrimeFactorFeature(PossibilitiesFeature):
    htype: House.Type
    row_column: int
    count: int

    TABLE: ClassVar[Dict[int, Sequence[Tuple[int, ...]]]] = None

    @staticmethod
    def all(htype: House.Type, counts: Sequence[int]) -> Sequence['PrimeFactorFeature']:
        return [PrimeFactorFeature(htype, rc, count) for rc, count in enumerate(counts, start=1)]

    def __init__(self, htype: House.Type, row_column: int, count: int):
        name = f'Row {htype.name.title()} #{row_column}'
        squares = self.get_row_or_column(htype, row_column)
        self.htype = htype
        self.row_column = row_column
        self.count = count
        if not PrimeFactorFeature.TABLE:
            PrimeFactorFeature.TABLE = self.generate_table()

        super().__init__(name, squares, compressed=True)

    def get_possibilities(self) -> Iterable[Tuple[Set[int], ...]]:
        return self._get_possibilities(self.count)

    @classmethod
    @lru_cache(None)
    def _get_possibilities(cls, count: int) -> Iterable[Tuple[Set[int], ...]]:
        return list(cls.fix_possibilities(cls.TABLE[count]))

    def draw(self, context: dict) -> None:
        self.draw_outside(self.count, self.htype, self.row_column, is_right=True, fontsize=15)

    @staticmethod
    def generate_table() -> Dict[int, Sequence[Tuple[int, ...]]]:
        if os.path.exists("/tmp/primes.pcl"):
            with open("/tmp/primes.pcl", "rb") as file:
                return pickle.load(file)

        i = 0
        keys = (9, 12, 24, 36, 40, 48, 96, 315, 400, 672)
        result = {key: [] for key in keys}
        for permutation in itertools.permutations('123456789'):
            i += 1
            if i % 10000 == 0:
                print(i)
            number = int(''.join(permutation))
            count = divisor_count(number)
            if count in result:
                result[count].append(tuple(map(int, permutation)))

        with open("/tmp/primes.pcl", "wb") as file:
            pickle.dump(result, file)
        return result


class Magpie218Solver:
    def run(self, show=False):
        features = [
            *PrimeFactorFeature.all(House.Type.ROW, [400, 96, 12, 315, 24, 12, 48, 24, 36]),
            *PrimeFactorFeature.all(House.Type.COLUMN, [9, 24, 24, 40, 672, 12, 24, 36, 12]),
        ]
        puzzle = "291--X--1..X--.1.-2..4..XX-8....7".replace("X", "---").replace("-", "...")
        puzzle = "..1--X--1..X--.1.-2..4..XX-......".replace("X", "---").replace("-", "...")
        puzzle = "..1--X--1..X--.1.-......XX-......".replace("X", "---").replace("-", "...")
        puzzle = "XXXXXXXXX".replace("X", "---").replace("-", "...")
        sudoku = Sudoku()
        if sudoku.solve(puzzle, features=features, show=show):
            grid = sudoku.grid
            for row in range(1, 10):
                cells = [grid.matrix[row, column] for column in range(1, 10)]
                value = int(''.join([str(cell.known_value) for cell in cells]))
                print(f"Row {row}: {value} = {self.pretty_print(prime_factors(value))}")
            for column in range(1, 10):
                cells = [grid.matrix[row, column] for row in range(1, 10)]
                value = int(''.join([str(cell.known_value) for cell in cells]))
                print(f"Col {column}: {value} = {self.pretty_print(prime_factors(value))}")

    @classmethod
    def show(cls):
        numbers = [
            291637584, 436581792, 578942163, 847159236, 962374815, 315268479, 723416958, 684795321, 159823647,
            245893761, 937461285, 168725349, 659132478, 384576192, 712948653, 571284936, 896317524, 423659817,
        ]
        for number in numbers:
            factors = prime_factors(number)
            print(f"{number} {factor_count(number):>3} {cls.pretty_print(factors)}")

    @staticmethod
    def pretty_print(factors: Sequence[Tuple[int, int]]) -> str:
        digits = '\u2070\u20b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079'
        result = []
        for (prime, power) in factors:
            if power == 1:
                result.append(str(prime))
            else:
                powerx = ''.join(digits[ord(x) - 48] for x in str(power))
                result.append(str(prime) + powerx)
        return ' × '.join(result)


if __name__ == '__main__':
    Magpie218Solver().run()
