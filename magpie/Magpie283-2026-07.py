import itertools
from collections.abc import Sequence
from functools import cache
from typing import Unpack

from more_itertools import is_prime

from solver import (
    AbstractClueValue,
    Clue,
    Clues,
    ClueValue,
    ConstraintSolver,
    DrawGridKwargs,
    LCH_Info,
    LetterCountHandler,
)
from solver.helpers import (
    digit_product,
    digit_sum,
    is_cube,
    is_fibonacci,
    is_square,
    is_triangular,
)


class TaggedString(AbstractClueValue):
    """Clue string plus a tag; subtype of ``AbstractClueValue``."""

    __slots__ = ('tag',)

    def __init__(self, value: int | str, tag: int) -> None:
        super().__init__(str(value))
        self.tag = tag

    @property
    def value(self) -> str:
        return self._text

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TaggedString):
            return self._text == other._text and self.tag == other.tag
        return NotImplemented

    def __hash__(self) -> int:
        return hash((self._text, self.tag))

    def __lt__(self, other: object) -> bool:
        if isinstance(other, TaggedString):
            return (self._text, self.tag) < (other._text, other.tag)
        return NotImplemented

    def __str__(self) -> str:
        return self._text

    def __repr__(self) -> str:
        from misc import subscript_digits
        return self._text + subscript_digits[self.tag + 1]


ACROSS_LENGTHS1 = "23/131/212/131/32"
DOWN_LENGTHS1 = "32/32/131/23/23"

ACROSS_LENGTHS2 = "32/131/212/131/23"
DOWN_LENGTHS2 = "23/23/131/32/32"


@cache
def pi_sum(pi, sum):
    return [i for i in range(10, 1000) if pi * digit_product(i) == sum * digit_sum(i)]


PERFECT = [28, 496]
LUCAS = [11, 18, 29, 47, 76, 123, 199, 322, 521, 843]
CATALAN = [14, 42, 132, 429]
FIBONACCI = [x for x in range(10, 1000) if is_fibonacci(x)]
PRIME = [x for x in range(10, 1000) if is_prime(x)]
SQUARE = [x for x in range(10, 1000) if is_square(x)]
CUBE = [x for x in range(10, 1000) if is_cube(x)]
TRIANGULAR = [x for x in range(10, 1000) if is_triangular(x)]
PI_IS_PRIME = [x for x in range(10, 1000) if is_prime(digit_product(x))]
PALINDROME = [x for x in range(10, 1000) if str(x) == str(x)[::-1]]
ODD = list(range(11, 1000, 2))
EVEN_DIGITS = [x for x in range(10, 1000) if set(str(x)) <= {"2", "4", "6", "8", "0"}]
SUM_IS_ONE = [x for x in range(10, 1000) if digit_sum(x) == 1]
PRODUCT_IS_ZERO = [x for x in range(10, 1000) if digit_product(x) == 0]
MULTIPLE_OF_BOTH_PI_AND_SUM = [x for x in range(10, 1000)
                         if (dp := digit_product(x)) != 0 and x % dp == 0 and x % digit_sum(x) == 0]
PI_PLUS_SUM = [x for x in range(10, 1000) if x == digit_sum(x) + digit_product(x)]
POWER_OF_TWO = {16, 32, 64, 128, 256, 512}
PI_OVER_SUM_IS_2_DIGITS = [x for x in range(10, 1000)
                      if (qr := divmod(digit_product(x), digit_sum(x))) and 100 > qr[0] >= 10 and qr[1] == 0]
PI_OVER_SUM_IS_3_DIGITS = [x for x in range(10, 1000)
                      if (qr := divmod(digit_product(x), digit_sum(x))) and 1000 > qr[0] >= 100 and qr[1] == 0]
ALL = list(range(10, 1000))


def tagged_generator(*list_of_lists):
    def generator(_clue):
        result = [TaggedString(item, tag)
                  for tag, list_ in enumerate(list_of_lists)
                  for item in list_]
        return result  # noqa
    return generator


class Magpie283(ConstraintSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.add_constraints_and_generators()
        # left, right = {0, 2, 3, 6, 7}, {1, 4, 5, 8, 9}
        solver.get_left_right()
        solver.solve(debug=True, max_debug_depth=100)

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues, letter_handler=MyLetterHandler())

    def get_clues(self) -> Sequence[Clue]:
        clues = []
        info1 = Clues.clue_info_from_clue_sizes(ACROSS_LENGTHS1, DOWN_LENGTHS1)
        info2 = Clues.clue_info_from_clue_sizes(ACROSS_LENGTHS2, DOWN_LENGTHS2)
        for is_left, info in ((True, info1), (False, info2)):
            suffix = "<" if is_left else ">"
            across_names, down_names = list("ABCDEFGH"), list("abcdefghj")
            keys = sorted(info, key=lambda x: (not x[1], x[0]))
            for key in keys:
                (_, is_across), (_, (r, c), length) = key, info[key]
                name = (across_names if is_across else down_names).pop(0) + suffix
                location = (r, c) if is_left else (r + 6, c)
                clues.append(Clue(name, is_across, location, length))
        return clues

    def add_constraints_and_generators(self):
        # A Π = 2Σ // 2Π = Σ // Π = 2Σ   Only one can have tag=1
        # [36, 44, 63, 138, 145, 154, 183, 224, 242, 318, 381, 415, 422, 451, 514, 541, 813, 831]
        # [11, 112, 121, 211]

        clue1, clue2 = self.clue_named("A<"), self.clue_named("A>")
        clue1.generator = clue2.generator = tagged_generator(pi_sum(1, 2), pi_sum(2, 1))
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != 1 or y.tag != 1)

        # B: Equals (Π + Σ)  // 3Π = 4Σ // Perfect
        clue1, clue2 = self.clue_named("B<"), self.clue_named("B>")
        clue1.generator = clue2.generator = tagged_generator(PI_PLUS_SUM, pi_sum(3, 4), PERFECT)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)

        # C: Sum of all digits in the grid // Lucas  // Fibonacci
        # The sum of the side that sums to 18 is 5x18=90, which isn't three digits.
        # The sum on the other side is 5x27=135. But 1+3+5+8+9 < 27, so we can't have all of 1, 3
        #     and 5 on the large side.
        clue1, clue2 = self.clue_named("C<"), self.clue_named("C>")
        clue1.generator = tagged_generator({}, LUCAS, FIBONACCI)
        clue2.generator = tagged_generator({}, LUCAS, FIBONACCI)

        # D:  Factor of both G and j // Odd // Palindrome
        clue1, clue2 = self.clue_named("D<"), self.clue_named("D>")
        clue1.generator = clue2.generator = tagged_generator(ALL, ODD, PALINDROME)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)
        self.dconstraint("DGj", lambda x, y, z: x.tag != 0 or (int(y) % int(x) == 0 and int(z) % int(x) == 0))

        # E: Power of 2 // Prime // Triangular
        clue1, clue2 = self.clue_named("E<"), self.clue_named("E>")
        clue1.generator = clue2.generator = tagged_generator(POWER_OF_TWO, PRIME, TRIANGULAR)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)

        # F: Square // Square // Cube     Both can't be cube.  We short cut this
        clue1, clue2 = self.clue_named("F<"), self.clue_named("F>")
        clue1.generator = clue2.generator = tagged_generator(SQUARE, {}, CUBE)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != 2 or y.tag != 2)

        # G:  Triangular // Triangular // A + H.
        # G=A+H can only be on the left side, and must yield a number starting with 1!
        clue1, clue2 = self.clue_named("G<"), self.clue_named("G>")
        clue1.generator = tagged_generator(TRIANGULAR, ALL)
        clue2.generator = tagged_generator(TRIANGULAR)
        self.add_constraint("G< A< H< ", lambda x, y, z:  x.tag != 1 or int(x) == int(y) + int(z))

        # H Square // Π is prime // Prime
        clue1, clue2 = self.clue_named("H<"), self.clue_named("H>")
        clue1.generator = clue2.generator = tagged_generator(SQUARE, PI_IS_PRIME, PRIME)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)

        # a: Contains only even digits // Lucas // 4Π = 7Σ
        clue1, clue2 = self.clue_named("a<"), self.clue_named("a>")
        clue1.generator = clue2.generator = tagged_generator(EVEN_DIGITS, LUCAS, pi_sum(4, 7))
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)

        # b: Triangular // Reverse of G // Π = Σa
        clue1, clue2 = self.clue_named("b<"), self.clue_named("b>")
        assert (clue1.length, clue2.length) == (3, 2)
        clue1.generator = tagged_generator(TRIANGULAR, ALL, PI_OVER_SUM_IS_2_DIGITS)
        clue2.generator = tagged_generator(TRIANGULAR, ALL, PI_OVER_SUM_IS_3_DIGITS)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)
        self.dconstraint("bG", lambda x, y: x.tag != 1 or str(x) == str(y)[::-1])
        self.dconstraint("ba", lambda x, y: x.tag != 2 or int(y) == digit_product(x) / digit_sum(x))

        # c: Cube // Triangular // Multiple of both Π and Σ
        clue1, clue2 = self.clue_named("c<"), self.clue_named("c>")
        clue1.generator = clue2.generator = tagged_generator(CUBE, TRIANGULAR, MULTIPLE_OF_BOTH_PI_AND_SUM)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)

        # d: Multiple of C // G * h // Prime
        # On the left side, d is length 2, so it can't be a multiple of C (3) or G x h.
        clue1, clue2 = self.clue_named("d<"), self.clue_named("d>")
        clue1.generator = tagged_generator({}, {}, PRIME)
        clue2.generator = tagged_generator(ALL, ALL)
        self.add_constraint("d> C>", lambda x, y: x.tag != 0 or int(x) % int(y) == 0)
        self.add_constraint("d> G> h>", lambda x, y, z: x.tag != 1 or int(x) == int(y) * int(z))

        # e: Σ = 1 //  Multiple of B // Π = 0
        clue1, clue2 = self.clue_named("e<"), self.clue_named("e>")
        clue1.generator = clue2.generator = tagged_generator(SUM_IS_ONE, ALL, PRODUCT_IS_ZERO)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)
        self.dconstraint("eB", lambda x, y: x.tag != 1 or int(x) % int(y) == 0)

        # f: Multiple of d // Prime// Factor of F
        clue1, clue2 = self.clue_named("f<"), self.clue_named("f>")
        clue1.generator = clue2.generator = tagged_generator(ALL, PRIME, ALL)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)
        self.dconstraint("fd", lambda x, y: x.tag != 0 or int(x) % int(y) == 0)
        self.dconstraint("fF", lambda x, y: x.tag != 2 or int(y) % int(x) == 0)

        # g: e - B // Cube // Less than e
        clue1, clue2 = self.clue_named("g<"), self.clue_named("g>")
        clue1.generator = clue2.generator = tagged_generator(ALL, CUBE, ALL)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)
        self.dconstraint("geB", lambda x, y, z: x.tag != 0 or int(x) == int(y) - int(z))
        self.dconstraint("ge", lambda x, y: x.tag != 2 or int(x) < int(y))

        # h: Factor of H // Catalan // Reverse of A
        # h> has length 2, so can't be reverse of A on the right hand side
        clue1, clue2 = self.clue_named("h<"), self.clue_named("h>")
        clue1.generator = tagged_generator(ALL, CATALAN, ALL)
        clue2.generator = tagged_generator(ALL, CATALAN)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)
        self.dconstraint("hH", lambda x, y: x.tag != 0 or int(y) % int(x) == 0)
        self.dconstraint("hA", lambda x, y: x.tag != 2 or str(x) == str(y)[::-1])

        # j: Triangular // Multiple of D // Catalan
        clue1, clue2 = self.clue_named("j<"), self.clue_named("j>")
        clue1.generator = clue2.generator = tagged_generator(TRIANGULAR, ALL, CATALAN)
        self.add_constraint((clue1, clue2), lambda x, y: x.tag != y.tag)
        self.dconstraint("jD", lambda x, y: x.tag != 1 or int(x) % int(y) == 0)

    def dconstraint(self, letters, function):
        for suffix in ("<", ">"):
            clue_names = [x + suffix for x in letters]
            self.add_constraint(clue_names, function)

    def get_left_right(self):
        result = []
        for left in itertools.combinations(range(0, 10), 5):
            if sum(left) not in (18, 27):
                continue
            left_set = frozenset(str(x) for x in left)
            right_set = frozenset(str(x) for x in range(10) if x not in left)
            for clue_name in ["B<", "B>", "A>", "C<"]:
                clue = self.clue_named(clue_name)
                values0 = [x for x in clue.generator(clue) if len(str(x)) == clue.length]
                values = [str(value) for value in values0]
                my_set = left_set if clue.name.endswith('<') else right_set
                if not any(set(str(x)) <= my_set for x in values):
                    break
            else:
                result.append((left_set, right_set))

        assert len(result) == 1
        str_left_set, str_right_set = result[0]
        for clue in self.clue_list:
            this_set = str_left_set if clue.name.endswith("<") else str_right_set
            self.add_constraint((clue,), lambda x, this_set=this_set: set(x) <= this_set)

    def draw_grid(self, **args: Unpack[DrawGridKwargs]) -> None:
        args['blacken_unused'] = False
        lcn = args['location_to_clue_numbers']
        for key, values in lcn.items():
            values = [x[0] for x in values]
            if len(values) == 1 and values[0].islower():
                values = ["", values[0]]
            lcn[key] = values
        args['font_multiplier'] = 0.8
        super().draw_grid(**args)


class MyLetterHandler(LetterCountHandler):
    def real_checking_value(self, value: ClueValue, _info: LCH_Info) -> bool:
        counter = self.counter
        return all(x <= 5 for x in counter.values())


if __name__ == '__main__':
    Magpie283.run()
