import itertools
from typing import Iterator, Callable, Iterable

from GenericSolver import ClueValueGenerator, Clue, Location, ClueValue, ClueList, SolverByClue

BASE = 9

def to_base(num: int, base: int = BASE) -> str:
    result = []
    if not num:
        return '0'
    while num:
        num, mod = divmod(num, base)
        result.append('0123456789ABCDEF'[mod])
    result.reverse()
    return ''.join(result)


def fixup(function:Callable[[], Iterable[int]]) -> ClueValueGenerator:
    def getter(clue: Clue) -> Iterator[ClueValue]:
        min_value = BASE ** (clue.length - 1)
        max_value = min_value * BASE
        for value in itertools.takewhile(lambda x: x < max_value, itertools.dropwhile(lambda x: x < min_value, function())):
            yield ClueValue(to_base(value))
    return getter

@fixup
def triangular() -> Iterable[int]:
    for i in itertools.count(1):
        yield i * (i + 1) // 2


@fixup
def square() -> Iterable[int]:
    for i in itertools.count(1):
        yield i * i


@fixup
def cube() -> Iterable[int]:
    for i in itertools.count(1):
        yield i * i * i


@fixup
def fibonacci() -> Iterable[int]:
    i, j = 1, 2
    while True:
        yield i
        i, j = j, i + j


@fixup
def lucas() -> Iterable[int]:
    i, j = 2, 1
    while True:
        yield i
        i, j = j, i + j


@fixup
def prime() -> Iterable[int]:
    return 2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97


def palindrome(clue: Clue) -> Iterable[ClueValue]:
    half_length = (clue.length + 1) // 2
    is_even = (clue.length & 1) == 0
    for i in range(BASE ** (half_length - 1), BASE ** (half_length)):
        left = to_base(i)
        right = left[::-1]
        yield ClueValue(left + (right if is_even else right[1:]))


def make(name: str, base_location: Location, length: int, generator: ClueValueGenerator) -> Clue:
    return Clue.make(name, name[0] == 'A', base_location, length, generator=generator)


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
    global BASE
    clue_list = ClueList(CLUES)
    clue_list.verify_is_180_symmetric()
    for BASE in range(2, 17):
        solver = SolverByClue(clue_list)
        solver.solve()
        print(BASE, solver.count_total)

if __name__ == '__main__':
    run()
