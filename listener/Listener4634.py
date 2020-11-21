import itertools
from collections import defaultdict, Counter
from typing import Sequence, Dict, List, Tuple, Any, cast

from solver import Clue, generators
from solver import ConstraintSolver
from solver import Location
from solver.constraint_solver import KnownClueDict


def roman_numeral_for(n: int) -> [str]:
    (a, b, c, d) = cast(Tuple, f'{n:04}')
    result = ["", "M", "MM", "MMM"][int(a)] + \
             ["", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"][int(b)] + \
             ["", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"][int(c)] + \
             ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"][int(d)]
    if len(result) <= 3 and ('M' in result or 'D' in result):
        return []
    return [RomanString(result, n)]


class RomanString(str):
    def __repr__(self) -> str:
        return f'RomanString("{str(self)}",{self.as_int})'

    def __new__(cls, value: str, as_int: int) -> Any:
        return super().__new__(cls, value)  # type: ignore

    def __init__(self, value: str, as_int: int) -> None:
        super().__init__()
        self.as_int = as_int
        self.has_special = 'M' in value or 'D' in value


def build_table() -> Tuple[Dict[int, Sequence[str]], Dict[str, int]]:
    result = defaultdict(list)
    result2: [str, int] = {}
    for prime in generators.prime_generator():
        if prime > 3999:
            break
        romans = roman_numeral_for(prime)
        for roman in romans:
            result[len(roman)].append(roman)
            assert roman not in result2
            result2[roman] = prime
    return result, result2


PRIME_TO_ROMAN_TABLE, ROMAN_TO_INT_TABLE = build_table()


class Listener4634(ConstraintSolver):
    all_results: List[Sequence[int]]

    @staticmethod
    def run():
        solver = Listener4634()
        solver.verify_is_180_symmetric()
        solver.solve(debug=True)
        print('SOLUTIONS = [')
        for line in solver.all_results:
            print(f'    {line},')
        print(']')

    def __init__(self,) -> None:
        super().__init__(self.get_clue_list())
        self.all_results = []
        self.add_my_constraints()

    def get_clue_list(self) -> [Clue]:
        def make(name: str, length: int, base_location: Location) -> 'Clue':
            return Clue(name, name.isupper(), base_location, length, generator=self.my_generator)

        return (
            make('A', 5, (1, 1)),
            make('B', 3, (1, 7)),
            make('C', 9, (2, 1)),
            make('D', 6, (3, 3)),
            make('E', 4, (4, 5)),
            make('F', 3, (5, 1)),
            make('G', 3, (5, 4)),
            make('H', 3, (5, 7)),
            make('I', 4, (6, 2)),
            make('J', 6, (7, 2)),
            make('K', 9, (8, 1)),
            make('L', 3, (9, 1)),
            make('M', 5, (9, 5)),

            make('a', 7, (1, 1)),
            make('b', 4, (1, 2)),
            make('c', 5, (1, 3)),
            make('d', 5, (1, 6)),
            make('e', 4, (1, 7)),
            make('f', 2, (1, 9)),
            make('g', 3, (2, 4)),
            make('h', 7, (3, 9)),
            make('i', 3, (4, 5)),
            make('j', 5, (5, 4)),
            make('k', 5, (5, 7)),
            make('l', 4, (6, 3)),
            make('m', 3, (6, 6)),
            make('n', 4, (6, 8)),
            make('o', 2, (8, 1))
        )

    @staticmethod
    def my_generator(clue: Clue) -> Sequence[str]:
        return PRIME_TO_ROMAN_TABLE[clue.length]

    def add_my_constraints(self) -> None:
        def clues_of_length(n: int) -> Sequence[Clue]:
            result = [clue for clue in self._clue_list if clue.length == n]
            assert len(result) == 2
            return result

        def test9922(nine1: RomanString, nine2: RomanString, two1: RomanString, two2: RomanString) -> bool:
            for a, b in itertools.permutations((two1.as_int, two2.as_int)):
                for s, t in itertools.permutations((nine1.as_int, nine2.as_int)):
                    if s + b == t + a:
                        return True
            return False

        def test77(seven1: RomanString, seven2: RomanString) -> bool:
            for q, r in itertools.permutations((seven1.as_int, seven2.as_int)):
                if q + 15 == 4 * r:
                    return True
            return False

        def test2266(two1: RomanString, two2: RomanString, six1: RomanString, six2: RomanString) -> bool:
            for a in (two1.as_int, two2.as_int):
                for (n, p) in itertools.permutations((six1.as_int, six2.as_int)):
                    if 2 * n == 2 * p + a + 3:
                        return True
            return False

        self.add_constraint((*clues_of_length(9), *clues_of_length(2)), test9922)
        self.add_constraint(clues_of_length(7), test77)
        self.add_constraint((*clues_of_length(2), *clues_of_length(6)), test2266)

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        special_count = sum(1 for value in known_clues.values() if cast(RomanString, value).has_special)
        if special_count != 3:
            return False
        location_to_value = {location: char
                             for clue, value in known_clues.items()
                             for location, char in zip(clue.locations, value)}
        temp = Counter(location_to_value.values())
        if temp['M'] != 1 or temp['D'] != 2:
            return False

        return self.check_all_constraints(known_clues)

    def check_all_constraints(self, known_clues):
        """
        In the equations below, lower-case letters stand for distinct grid entries, of the
        following lengths: a, b (2); c (3); d, e, f, g, h, k (4); m (5); n, p (6); q, r (7); s, t (9).
        Apart from the grouping by length, this list is in no particular order.
        d = Vt + c + n
        e + f + g + h + k + VII = s + m
        m + IV = s + IIa
        IIn = IIp + a + III
        q + XV = IVr
        s + b = t + a
        """
        answers = defaultdict(list)
        for roman in known_clues.values():
            answers[len(roman)].append(roman)
        for a, b in itertools.permutations(answers[2], 2):
            for c in answers[3]:
                for d in answers[4]:
                    temp = set(answers[4])
                    temp.remove(d)
                    e, f, g, h, k = list(temp)
                    for m in answers[5]:
                        for n, p in itertools.permutations(answers[6], 2):
                            for q, r in itertools.permutations(answers[7], 2):
                                for s, t in itertools.permutations(answers[9], 2):
                                    if (d.as_int == 5 * t.as_int + c.as_int + n.as_int
                                            and e.as_int + f.as_int + g.as_int + h.as_int + k.as_int + 7
                                                == s.as_int + m.as_int
                                            and m.as_int + 4 == s.as_int + 2 * a.as_int
                                            and 2 * n.as_int == 2 * p.as_int + a.as_int + 3
                                            and q.as_int + 15 == 4 * r.as_int
                                            and s.as_int + b.as_int == t.as_int + a.as_int):
                                        print(a, b, c, d, e, f, g, h, k, m, n, p, q, r, s, t)
                                        return True
        return False

    def show_solution(self, known_clues: KnownClueDict) -> None:
        values = [known_clues[clue]for clue in self._clue_list]
        self.all_results.append(values)
        super().show_solution(known_clues)

    def draw_grid(self, **args: Any) -> None:
        args['location_to_clue_numbers'].clear()
        super().draw_grid(**args)


if __name__ == '__main__':
    Listener4634.run()
