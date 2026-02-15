from collections import defaultdict
from itertools import combinations
from typing import Any

import math

from misc.factors import prime_factors
from misc.primes import PRIMES
from solver import Clue, ConstraintSolver, KnownClueDict
from solver.generators import allvalues, filterer, get_min_max, nth_power, square


def number_to_grid(n):
    q, r = divmod(n - 1, 10)
    if q % 2 == 0:
        return (10 - q, r + 1)
    else:
        return (10 - q, 10 - r)


GRID_TO_NUMBER = {number_to_grid(i): i for i in range(1, 101)}

assert len(GRID_TO_NUMBER) == 100

def grid_to_number(grid):
    return GRID_TO_NUMBER[grid]


SNAKES = [(42, 4), (61, 4), (68, 4), (94, 3)]
LADDERS = [(11, 4), (15, 4), (38, 3), (45, 5)]

MOVES = (5, 10, 46, 51, 56, 40, 85, 90, 95, 100)

def play_game():
    my_map = {}
    for accessory in (SNAKES, LADDERS):
        for start, length in accessory:
            start_row, col  = number_to_grid(start)
            end_row = start_row + (length - 1) if accessory is SNAKES else start_row - (length - 1)
            my_map[start] = grid_to_number((end_row, col))

    for die in range(1, 7):
        items = [die]
        while len(items) < 10:
            current = items[-1]
            next = min(current + die, 100)
            next = my_map.get(next, next)
            items.append(next)
        print(items)

class Listener4895(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=False)

    def __init__(self):
        clue_map = self.get_clues()
        super().__init__(list(clue_map.values()))
        self.add_my_constraints(clue_map)

    def get_clues(self) -> dict[str, Clue]:
        clue_map = {}
        for accessory in (SNAKES, LADDERS):
            for start, length in accessory:
                start_row, col = number_to_grid(start)
                locations = None
                if accessory is LADDERS:
                    locations = [(row, col) for row in range(start_row, start_row - length, -1)]
                    name = str(start) + 'u'
                else:
                    locations = None
                    name = str(start) + 'd'
                clue = Clue(name, False, (start_row, col), length, locations=locations)
                clue_map[name] = clue
        for row in range(1, 11):
            start = grid_to_number((row, 1))
            name = str(start) + 'a'
            clue = Clue(name, True, (row, 1), 10)
            clue_map[name] = clue

        # ACROSS
        clue_map['1a'].generator = nth_power(3)  # add highest
        clue_map['20a'].generator = nth_power(3) # add lowest
        for i in (21, 60, 61, 80, 81):
            clue_map[str(i) + 'a'].generator = prime_power_prime(1 if i == 21 else 0)
        clue_map['40a'].generator = nth_power(6)
        clue_map['41a'].generator = nth_power(3)
        clue_map['100a'].generator = nth_power(9)

        # SNAKES
        clue_map['42d'].generator = allvalues  # need to add conclusion
        clue_map['61d'].generator = nth_power(4)
        clue_map['68d'].generator = allvalues # five_primes
        clue_map['94d'].generator = allvalues  # need to add conclusion

        # LADDERS
        clue_map['11u'].generator = filterer(lambda x: x ** 3 < 10_000_000_000) # plus 41a
        clue_map['15u'].generator = double_square
        clue_map['38u'].generator = allvalues  # need to add conclusion
        clue_map['45u'].generator = square
        return clue_map

    def add_my_constraints(self, clue_map):
        for i in (21, 40, 41, 60, 61, 80, 81, 100):
            other = clue_map[str(i) + 'a']
            self.add_constraint((clue_map['1a'], other), lambda x, y: x > y, name=f"1 > {i}")
            self.add_constraint((clue_map['20a'], other), lambda x, y: x < y, name=f"20 < {i}")

        self.add_constraint('11u 41a', lambda x, y: int(x) ** 3 == int(y))
        self.add_constraint('94d 42d', lambda x, y: math.gcd(int(x), int(y)) >= 10)

        locations = defaultdict(list)
        for clue in clue_map.values():
            for index, location in enumerate(clue.locations):
                locations[grid_to_number(location)].append((clue, index))
        for move1, move2 in combinations(MOVES, 2):
            for clue1, index1 in locations[move1]:
                for clue2, index2 in locations[move2]:
                    if clue1 == clue2:
                        self.add_constraint((clue1,), (lambda x, ix1=index1, ix2=index2: x[ix1] != x[ix2]), name = f"{move1}/{move2}")
                    else:
                        self.add_constraint((clue1, clue2), (lambda x, y, ix=index1, iy=index2: x[ix] != y[iy]), name = f"{move1}/{move2}")

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        board = {location: int(value) for clue, clue_value in known_clues.items()
                 for location, value in zip(clue.locations, clue_value)}
        assert len(board) == 100
        total = sum(board.values())
        evens = sum(x % 2 == 0 for x in board.values())
        print(total, evens, known_clues[self.clue_named('1a')])
        if int(known_clues[self.clue_named('42d')]) % evens == 0:
            if int(known_clues[self.clue_named('94d')]) % evens == 0:
                return True
        return False

    def plot_board(self, clue_values: KnownClueDict | None = None,
                   **more_args: Any) -> None:
        coloring = {number_to_grid(i): 'red' for i in MOVES}

        super().plot_board(clue_values, left_bars={}, top_bars={},
                           location_to_clue_numbers={},
                           coloring=coloring)


def prime_power_prime(delta):
    def internal(clue):
        assert clue.length == 10
        primes = PRIMES
        two_digit_primes = [x for x in PRIMES if 10 <= x <= 99]
        for p in two_digit_primes:
            power = int(math.log(1e10) / math.log(p))
            assert p ** power + delta < 10_000_000_000
            assert p ** (power + 1) + delta >= 10_000_000_000
            if len(str(p ** power + delta)) == 10 and power in primes:
                yield p ** power + delta
    return internal

def five_primes(clue):
    min_value, max_value = get_min_max(clue)
    for value in range(min_value, max_value):
        temp = prime_factors(value)
        if len(temp) == 5:
            if all(y == 1 for _, y in temp):
                yield value

def double_square(clue):
    min_value, max_value = get_min_max(clue)
    lower = int(math.ceil(math.sqrt(min_value / 2)))
    upper = int(math.ceil(math.sqrt(max_value / 2)))
    return map(lambda x: 2 * x * x, range(lower, upper))

if __name__ == '__main__':
    Listener4895.run()
