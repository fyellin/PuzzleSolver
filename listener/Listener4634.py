import itertools
from collections import defaultdict, Counter
from collections.abc import Sequence
from typing import Any, cast

from solver import Clue, generators
from solver import ConstraintSolver
from solver import Location, KnownClueDict


def roman_numeral_for(n: int) -> [str]:
    (a, b, c, d) = cast(tuple, f'{n:04}')
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


def build_table() -> tuple[dict[int, Sequence[str]], dict[str, int]]:
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
    @staticmethod
    def run():
        solver = Listener4634()
        solver.verify_is_180_symmetric()
        solver.solve(debug=True)

    def __init__(self,) -> None:
        super().__init__(self.make_clue_list())
        self.add_my_constraints()

    def make_clue_list(self) -> [Clue]:
        counter = 0

        def make(name: str, length: int, base_location: Location) -> 'Clue':
            nonlocal counter
            counter += 1
            return Clue(str(counter), name.isupper(), base_location, length, generator=self.my_generator)

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

        return bool(self.check_all_constraints(known_clues))

    @staticmethod
    def check_all_constraints(known_clues: KnownClueDict) -> dict[str, int] | None:
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
            answers[len(roman)].append(cast(RomanString, roman))

        dtcn = [(d, t, c, n) for d, t, c, n in itertools.product(answers[4], answers[9], answers[3], answers[6])
                if d.as_int == 5 * t.as_int + c.as_int + n.as_int]
        dsm = [(d, s, m) for d, s, m in itertools.product(answers[4], answers[9], answers[5])
               for e, f, g, h, k in [sorted(set(answers[4]) - {d})]
               if e.as_int + f.as_int + g.as_int + h.as_int + k.as_int + 7 == s.as_int + m.as_int]
        msa = [(m, s, a) for m, s, a in itertools.product(answers[5], answers[9], answers[2])
               if m.as_int + 4 == s.as_int + 2 * a.as_int]
        npa = [(n, p, a) for (n, p), a in itertools.product(itertools.permutations(answers[6], 2), answers[2])
               if 2 * n.as_int == 2 * p.as_int + a.as_int + 3]
        qr = [(q, r) for q, r in itertools.permutations(answers[7], 2)
              if q.as_int + 15 == 4 * r.as_int]
        sbta = [(s, b, t, a)
                for s, t in itertools.permutations(answers[9], 2)
                for a, b in itertools.permutations(answers[2], 2)
                if s.as_int + b.as_int == t.as_int + a.as_int]

        for (d, t, c, n), (d2, s, m), (m2, s2, a), (n, p, a2), (q, r), (s3, b, t, a3) \
                in itertools.product(dtcn, dsm, msa, npa, qr, sbta):
            if d == d2 and a == a2 == a3 and m == m2 and s == s2 == s3:
                e, f, g, h, k = sorted(set(answers[4]) - {d})
                my_dict = {letter: value for letter, value in zip("abcdefghkmnpqrst",
                                                                  (a, b, c, d, e, f, g, h, k, m, n, p, q, r, s, t))}
                return my_dict

        return None

    def draw_grid(self, **args: Any) -> None:
        location_to_clue_numbers = defaultdict(list)
        clue_values: KnownClueDict = args['clue_values']
        for letter, value in self.check_all_constraints(clue_values).items():
            clue = next(clue for clue in self._clue_list if clue_values[clue] == value)
            pointer = '→' if clue.is_across else '↓'
            location_to_clue_numbers[clue.location(0)].append(letter + pointer)
        args['location_to_clue_numbers'] = location_to_clue_numbers
        super().draw_grid(**args)


if __name__ == '__main__':
    Listener4634.run()
