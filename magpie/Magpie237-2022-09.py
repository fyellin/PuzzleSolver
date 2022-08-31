import dataclasses
import itertools
import re
from collections import Counter
from typing import Any, Iterator, Sequence

from matplotlib.patches import Arc

from solver import Clue, Clues, ConstraintSolver, Intersection, generators

GRID = """
x.xxxxxx
x...x...
xx....x.
.x.x.x..
x.xx...x
x...xx..
.x..x...
x..x....
"""

ACROSSES = """
a 5 S**5 - A**3
e 3 Palindrome
h 4 Fibonacci - AU - E
i 3 T**2(S + T)
j 4 Cube - A
l 2 CTU
m 4  C**2ES(S + U) + L!
o 3 C**3 + E**3 + T**3
p 3 A**5 - A + C**5 - C
r 4 Square - A
t 2 Fibonacci
u 4 Square * E
w 3 Perfect * (A + S) - CT
x 4 Cube * E - AS
y 3 CU(E + T)
z 5  A + U!(EU)
"""

DOWNS = """
a 4 Cube - U**2
b 3 EU(S + U) – O 
c 3 Square
d 5 S! S/C + T**4
e 4 S**2(A + T**2)
f 2 S (O + S)
g 4 Fibonacci × A + CE
k 4 Prime + T
l 4 Prime + A
n 5 A + (A + U)**4 * C
p 4 Triangular * S + C**5
q 4 A**2 S**3 + (A + S)/C
s 4 A(S + TU)**2
u 3 (EU + O)U
v 3 ES(S + T)
w 2 Triangular + L!
"""

generators.BASE = 8


@dataclasses.dataclass
class MyIterator:
    base: Iterator[int]
    multiplier: int = 1
    offset: int = 0

    def __iter__(self) -> Iterator[int]:
        for x in self.base:
            yield x * self.multiplier + self.offset

    def __add__(self, other):
        return MyIterator(self.base, self.multiplier, self.offset + other)

    def __sub__(self, other):
        return MyIterator(self.base, self.multiplier, self.offset - other)

    def __mul__(self, other):
        if other != 0:
            return MyIterator(self.base, self.multiplier * other, self.offset * other)
        else:
            assert other != 0

    def generator(self):
        def result(clue: Clue):
            min_value, max_value = 8 ** (clue.length - 1), 8 ** clue.length
            for value in self:
                if value >= min_value:
                    if value >= max_value:
                        return
                    yield octal(value)
        return result


def palindrome():
    return generators.palindrome


def fibonacci():
    def fib_generator():
        i, j = 1, 2
        while True:
            yield i
            i, j = j, i + j
    return MyIterator(fib_generator())


def cube():
    return MyIterator(x**3 for x in itertools.count(1))


def square():
    return MyIterator(x**2 for x in itertools.count(1))


def perfect():
    return MyIterator([6, 28, 496, 8128])


def prime():
    return MyIterator(generators.prime_generator())


def triangular():
    return MyIterator((x * (x + 1)) // 2 for x in itertools.count(1))


MAPPING = dict(Palindrome=palindrome,
               Fibonacci=fibonacci, Cube=cube, Square=square,
               Perfect=perfect, Prime=prime, Triangular=triangular)


SPECIALS = set(MAPPING.keys())


def octal(result):
    return oct(result)[2:]


class Solver237(ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Solver237()
        solver.verify_is_180_symmetric()
        solver.solve()

    def __init__(self) -> None:
        clues = self.get_clue_list()
        super().__init__(clues)
        self.values = self.get_letters_and_fixed_clues()
        for clue in clues:
            if clue in self.values:
                clue.generator = generators.known(self.values[clue])
            else:
                evaluator = clue.evaluators[0]
                result = evaluator.callable(*(self.values[x] for x in evaluator.vars))
                if isinstance(result, MyIterator):
                    clue.generator = result.generator()
                else:
                    clue.generator = result

    def draw_grid(self, **args: Any) -> None:
        converter = {"0": "w", "4": "w", "1": "x", "2": "x",
                     "3": "y", "5": "y", "6": "z", "7": "z"}
        curve = {}
        missing = 0
        items = args['location_to_entry']
        for row, column in itertools.product(range(1, 5), repeat=2):
            values = [converter[items[i, j]]
                      for i in (row, row + 4) for j in (column, column + 4)]
            counter = Counter(values)
            (letter, max_count), = counter.most_common(1)
            for i in (row, row + 4):
                for j in (column, column + 4):
                    curve[i, j] = letter
            missing += (4 - max_count)
        assert missing == 8

        args.pop('location_to_clue_numbers')
        args['top_bars'] = args['left_bars'] = {}
        args['location_to_entry'].clear()
        super().draw_grid(extra=lambda plt, axes: self.extra(plt, axes, curve),
                          font_multiplier=.5, **args,
                          file="/Users/fy/Desktop/Magpie237.png")

        # for location, value in curve.items():
        #     items[location] = dict(w="LT", x="OC", y="AE", z="SU")[value]
        # super().draw_grid(extra=lambda plt, axes: self.extra(plt, axes, curve),
        #                   font_multiplier=.5, **args)

    def extra(self, plt, axes, curves):
        color = 'black'
        width = 3
        for (y, x), value in curves.items():
            match value:
                case 'z':
                    plt.plot((x + .5, x + .5), (y, y + 1), color, lw=width)
                    plt.plot((x + 0, x + .3), (y + .5, y + .5), color, lw=width)
                    plt.plot((x + .7, x + 1), (y + .5, y + .5), color, lw=width)
                case 'w':
                    plt.plot((x + 0, x + 1), (y + .5, y + .5), color, lw=width)
                    plt.plot((x + .5, x + .5), (y + .0, y + .3), color, lw=width)
                    plt.plot((x + .5, x + .5), (y + .7, y + 1.0), color, lw=width)
                case 'x':
                    axes.add_patch(Arc((x, y), width=1, height=1,
                                       theta1=0, theta2=90, color=color, lw=width))
                    axes.add_patch(Arc((x + 1, y + 1), width=1, height=1,
                                       theta1=180, theta2=270, color=color, lw=width))
                case 'y':
                    axes.add_patch(Arc((x + 1, y), width=1, height=1,
                                       theta1=90, theta2=180, color=color, lw=width))
                    axes.add_patch(Arc((x, y + 1), width=1, height=1,
                                       theta1=270, theta2=360, color=color, lw=width))

        axes.text(5, 9.2, "OSCULATE", fontsize=15,
                  fontweight='bold', fontfamily="sans-serif",
                  va='top', ha='center')

    def get_letters_and_fixed_clues(self):
        """
        Look at all possible mappings, and see which ones gives consistent answers for
        the clues consisting just of letters.
        """
        mappings = [dict(A=A, C=C, E=E, L=L, O=O, S=S, T=T, U=U)
                    for A, C, E, L, O, S, T, U in itertools.permutations(range(8))]
        seen = set()
        for clue in self._clue_list:
            if any(x in clue.expression for x in SPECIALS):
                continue
            seen.add(clue)
            intersections = [x for clue2, intersections in self._all_intersections[clue]
                             if clue2 in seen for x in intersections]
            pattern_generator = Intersection.make_pattern_generator(
                clue, intersections, self)
            next_mappings = []
            for mapping in mappings:
                try:
                    evaluator = clue.evaluators[0]
                    result = evaluator.callable(*(mapping[x] for x in evaluator.vars))
                except ArithmeticError:
                    continue
                if result == int(result) and result > 0:
                    pattern = pattern_generator(mapping)
                    entry = octal(int(result))
                    if pattern.fullmatch(entry):
                        mapping[clue] = entry
                        next_mappings.append(mapping)
            mappings = next_mappings
        assert len(mappings) == 1
        return mappings.pop()

    @classmethod
    def get_clue_list(cls) -> Sequence[Clue]:
        result = []
        locations = Clues.get_locations_from_grid(GRID)
        for lines, is_across, letter in ((ACROSSES, True, 'a'), (DOWNS, False, 'd')):
            for line in lines.splitlines():
                line = line.strip()
                if not line:
                    continue
                match = re.fullmatch(r'([a-z]) (\d) (.*)', line)
                assert match
                number, length, expression = match.group(1, 2, 3)
                number = ord(number) - ord('a') + 1
                length = int(length)
                location = locations[number - 1]
                for x in SPECIALS:
                    expression = expression.replace(x, '"' + x + '"()')
                clue = Clue(f'{number}{letter}', is_across, location, length)
                clue.expression = expression
                clue.evaluators = clue.create_evaluators(expression, mapping=MAPPING)
                result.append(clue)
        return result


if __name__ == '__main__':
    Solver237.run()
