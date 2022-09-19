import dataclasses
import itertools
import re
from collections import Counter
from enum import Enum, auto
from typing import Any, Iterable, Iterator, Optional, Sequence

from matplotlib.patches import Arc

from solver import Clue, ClueValue, Clues, ConstraintSolver, EquationSolver, Evaluator, \
    Letter, generators
from solver.constraint_solver import KnownClueDict
from solver.equation_solver import KnownLetterDict

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
    base: Optional[Iterator[int]] = None
    multiplier: int = 1
    offset: int = 0

    def __iter__(self) -> Iterator[str]:
        for x in self.base:
            yield x * self.multiplier + self.offset

    def __add__(self, other):
        return MyIterator(self.base, self.multiplier, self.offset + other)

    def __sub__(self, other):
        return MyIterator(self.base, self.multiplier, self.offset - other)

    def __mul__(self, other):
        assert other > 0
        return MyIterator(self.base, self.multiplier * other, self.offset * other)


def palindrome():
    return MyIterator(x for x in itertools.count(1) if octal(x) == octal(x)[::-1])


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


class Picture (Enum):
    ACROSS = auto()
    DOWN = auto()
    NW_SE = auto()
    NE_SW = auto()


class Solver237(ConstraintSolver):
    @staticmethod
    def run() -> None:
        solver = Solver237()
        solver.verify_is_180_symmetric()
        solver.solve()

    def __init__(self) -> None:
        clues = self.get_clue_list()
        super().__init__(clues)
        values = self.get_letter_values()
        for clue in clues:
            evaluator = clue.evaluators[0]
            clue.generator = lambda clue, evaluator=evaluator: itertools.takewhile(
                lambda x: len(x) <= clue.length, evaluator(values))

    def draw_grid(self, **args: Any) -> None:
        converter = {"0": Picture.ACROSS, "4": Picture.ACROSS,
                     "1": Picture.NW_SE, "2": Picture.NW_SE,
                     "3": Picture.NE_SW, "5": Picture.NE_SW,
                     "6": Picture.DOWN, "7": Picture.DOWN}
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
        # args['location_to_entry'].clear()
        super().draw_grid(extra=lambda plt, axes: self.extra(plt, axes, curve),
                          font_multiplier=.5, **args)

        # for location, value in curve.items():
        #     items[location] = dict(w="LT", x="OC", y="AE", z="SU")[value]
        # super().draw_grid(extra=lambda plt, axes: self.extra(plt, axes, curve),
        #                   font_multiplier=.5, **args)

    def extra(self, plt, axes, curves):
        color = 'black'
        width = 3
        for (y, x), value in curves.items():
            match value:
                case Picture.DOWN:
                    plt.plot((x + .5, x + .5), (y, y + 1), color, lw=width)
                    plt.plot((x + 0, x + .3), (y + .5, y + .5), color, lw=width)
                    plt.plot((x + .7, x + 1), (y + .5, y + .5), color, lw=width)
                case Picture.ACROSS:
                    plt.plot((x + 0, x + 1), (y + .5, y + .5), color, lw=width)
                    plt.plot((x + .5, x + .5), (y + .0, y + .3), color, lw=width)
                    plt.plot((x + .5, x + .5), (y + .7, y + 1.0), color, lw=width)
                case Picture.NW_SE:
                    axes.add_patch(Arc((x, y), width=1, height=1,
                                       theta1=0, theta2=90, color=color, lw=width))
                    axes.add_patch(Arc((x + 1, y + 1), width=1, height=1,
                                       theta1=180, theta2=270, color=color, lw=width))
                case Picture.NE_SW:
                    axes.add_patch(Arc((x + 1, y), width=1, height=1,
                                       theta1=90, theta2=180, color=color, lw=width))
                    axes.add_patch(Arc((x, y + 1), width=1, height=1,
                                       theta1=270, theta2=360, color=color, lw=width))

        axes.text(5, 9.2, "OSCULATE", fontsize=15,
                  fontweight='bold', fontfamily="sans-serif",
                  va='top', ha='center')

    def get_letter_values(self) -> KnownLetterDict:
        clues = [clue for clue in self._clue_list if clue.context]
        result = {}

        class Solver2(EquationSolver):
            def run(self):
                self.solve(debug=True)

            def show_solution(self, clue_values: KnownClueDict, known_letters: KnownLetterDict
                              ) -> None:
                nonlocal result
                result = dict(known_letters)
                self.plot_board(clue_values)

        Solver2(clues, items=range(8)).run()
        return result

    @staticmethod
    def base_eight_wrapper(evaluator: Evaluator, value_dict: dict[Letter, int]
                           ) -> Iterable[ClueValue]:
        try:
            result = evaluator.callable(*(value_dict[x] for x in evaluator.vars))
            if isinstance(result, MyIterator):
                for value in result:
                    yield(ClueValue(octal(value)))
                return
            int_result = int(result)
            if result == int_result > 0:
                yield ClueValue(octal(int_result))
        except ArithmeticError:
            pass

    def get_clue_list(self) -> Sequence[Clue]:
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
                original_expression = expression
                for x in SPECIALS:
                    expression = expression.replace(x, '"' + x + '"()')
                clue = Clue(f'{number}{letter}', is_across, location, length)
                clue.expression = expression
                clue.evaluators = clue.create_evaluators(
                    expression, mapping=MAPPING, wrapper=self.base_eight_wrapper)
                # Context indicates this clue has nothing special in it.
                clue.context = expression == original_expression
                result.append(clue)
        return result


if __name__ == '__main__':
    Solver237.run()
