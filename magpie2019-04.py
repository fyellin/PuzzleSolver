from typing import Iterator, Union
from GenericSolver import ClueValueGenerator, Clue, Location, ClueList, SolverByClue
import Generators
from Generators import triangular, lucas, fibonacci, square, cube, prime, palindrome


def convert_to_base(num: int, base: int) -> str:
    result = []
    if not num:
        return '0'
    while num:
        num, mod = divmod(num, base)
        result.append('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz<>'[mod])
    result.reverse()
    return ''.join(result)


def using_current_base(generator: ClueValueGenerator) -> ClueValueGenerator:
    def result(clue: Clue) -> Iterator[str]:
        def maybe_convert(value: Union[int, str]) -> str:
            return value if isinstance(value, str) else convert_to_base(value, Generators.BASE)
        return map(maybe_convert, generator(clue))
    return result


def make(name: str, base_location: Location, length: int, generator: ClueValueGenerator) -> Clue:
    return Clue.make(name, name[0] == 'A', base_location, length, generator=using_current_base(generator))


CLUES = (
    make('A1', (1, 1), 3, triangular),
    make('A3', (1, 4), 2, triangular),
    make('A4', (2, 1), 2, lucas),
    make('A5', (2, 3), 3, triangular),
    make('A8', (3, 2), 3, fibonacci),
    make('A10', (4, 1), 3, triangular),
    make('A12', (4, 4), 2, triangular),
    make('A14', (5, 1), 2, lucas),
    make('A15', (5, 3), 3, square),

    make('D1', (1, 1), 2, prime),
    make('D2', (1, 2), 3, palindrome),
    make('D3', (1, 4), 2, cube),
    make('D5', (2, 3), 3, fibonacci),
    make('D6', (2, 5), 2, lucas),
    make('D7', (3, 1), 2, square),
    make('D9', (3, 4), 3, square),
    make('D11', (4, 2), 2, cube),
    make('D13', (4, 5), 2, fibonacci)
)


def run() -> None:
    clue_list = ClueList.create(CLUES)
    clue_list.verify_is_180_symmetric()
    solver = SolverByClue(clue_list)

    for Generators.BASE in range(2, 65):
        print(f'Running in base {Generators.BASE}')
        solver.solve(show_time=False, debug=False)
        print(f'Using {solver.count_total} steps')

if __name__ == '__main__':
    run()
