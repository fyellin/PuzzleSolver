import itertools
import re
from typing import Any
from collections.abc import Iterable, Sequence

from solver import Clue, Clues, EquationSolver, Evaluator, equation_parser, Parse, \
    KnownLetterDict

CLUES = """
15 fh + mh = (l + z)h
2 (g − n − q)h + (a + c)h = fh
12ac (u + y)h + (v + x)h = (c + qz)h 
26 (d + g)h + (l + y)h = (qz)h
30dn ch + ph = qh
31 ki + ni = (k + n)i
8 (m − t)c + (y − l)c = (qt − kz)c 
20 (qt − kz)c + (m − z)c = (g − r)c 
24 qc + (m − t)c = (x − l)c
10ac dh + (t + y)h = (cu)h
6 (v−a)h + dh = eh
9 (k + n)h + (i + x)h = (d + f)h
32 (t + v)c + (jp + r)c = (cnq)c
28 (f + j)h + (eq)h = (b + f + g)h 
7ac ih +ph =qh
25dn rh + vh = mh
29 (e − k)h + (l − a)h = (u − n)h
22 (e + u)h + (cj)h = (b + x + y)h
23 (x − g)h + (e − q)h = (d + q − o)h
1ac (k + n)q + (g − o)q = (o + u − q)q
10dn (s − d)c + (ev − of)c = zc
17 ph + (c + m − e)h = th
14 hh + (c + q)h = dh
12dn (q**c)h + (q**c + b)h = (bd − q)h
21 (p + w)c + (hw + k)c = (hw + o)c 
5 hh +dh =eh
1dn (mq − e)h + (cez + e)h = (cez + j)h 
18 (r + u)c + (gh + hu)c = (nz)c
7dn oh + eh = (y − u)h
11 (t − p)c + (t − i)c = (i + t)c
30ac (y − f)h + uh = (p + r)h
25ac (c + h + q)h + (g + j + m)h = (l+x+y)h
4 (j + y)h + (mp)h = (fq − c)h
27 oh +ah =vh
3 (hy − k − x)p + (i + nq)p = (f + v)p 
13 (mqz)h + (lq**c + i)h = (hjqz)h
16 (bp)h + (ef)h = (fz − i)h
19 (k**p − hk − hn)h + (k**p + p**p − c)h = (he**c + c)h
"""

ACROSS = "11111111111/1721/111341/14411/125111/11711/111521/11441/1431111/1271/11111111111"
DOWN = "11111111111/1631/13331/1721/14411/12521/11441/1271/13331/1361/11111111111"

CLUE_EXTRAS = ("21.10ac.8.1dn.11.14.10dn.30ac.20.28.8.1dn.5.7ac.22.32.17.1ac.10dn.25dn.18.12dn.29.6."
               "7ac.28.21.14.20.32.5.24.23.9.1ac.22.29.7dn".split('.'))


class MyString(str):
    def __repr__(self) -> str:
        return self.__str__()

    def __new__(cls, value: str, delta: int) -> Any:
        return super().__new__(cls, value)  # type: ignore

    def __init__(self, value: str, delta: int) -> None:
        super().__init__()
        self.value = value
        self.delta = delta

    def __eq__(self, other) -> bool:
        return other is not None and (self.value, self.delta) == (other.value, other.delta)

    def __hash__(self) -> int:
        return hash((self.value, self.delta))

    def __lt__(self, other) -> bool:
        return (self.value, self.delta) < (other.value, other.delta)


@lambda _: _()
def clue_equations():
    parser = equation_parser.EquationParser()
    clue_info = []
    for line in CLUES.strip().splitlines():
        match = re.fullmatch(r'(\d\d?)(ac|dn|) (.*)', line)
        number = match.group(1) + match.group(2)
        left, right = parser.parse(match.group(3))
        assert left.expression[0] == '+'
        x, y, z = left.expression[1], left.expression[2], right.expression
        assert len(x) == len(y) == len(z) == 3
        clue_info.append((number, x[1], y[1], z[1], x[2]))
    return clue_info


class Listener4843(EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.solve(debug=True)

    def __init__(self):
        clue_list = self.get_clues()
        self.fake_clues = clue_list[-4:]
        super().__init__(clue_list, items=range(1, 27))

        self.clue_extras = [self.clue_from_name(name) for name in CLUE_EXTRAS]

        mapping = {'pyth': self.pyth}
        normal_clues = []
        for index, (name, x, y, z, h) in enumerate(clue_equations):
            clue = self.clue_from_name(name)
            equation = str(Parse(('function', 'pyth', (x, y, z, h))))
            clue.evaluators = Evaluator.create_evaluators(equation, mapping, self.my_wrapper)
            if clue not in self.clue_extras:
                if not normal_clues:
                    self.add_constraint((clue,), lambda x: x.delta == 0)
                else:
                    self.add_constraint((clue,), lambda x: x.delta > 26)
            else:
                normal_clues.append(clue)
                self.add_constraint((clue,), lambda x: 1 <= x.delta <= 26)
        for clue1, clue2 in itertools.combinations(normal_clues, 2):
            self.add_constraint((clue1, clue2), lambda x, y: x.delta <= y.delta)

        self.exponents = {h for (*_, (_, h)) in clue_equations}

    def get_clues(self):
        clue_list = Clues.clues_from_clue_sizes(ACROSS, DOWN)
        clue_list.extend([
            Clue('', True, (1, 1), 10),
            Clue('', False, (1, 11), 10),
            Clue('', True, (11, 2), 10),
            Clue('', False, (4, 1), 8)
        ])
        return clue_list

    @staticmethod
    def pyth(a, b, c, h):
        if not (0 < a < b < c):
            return -1, 0
        if not 1 <= h <= 5:
            return -1, 0
        value = a ** h + b ** h
        error = abs(c ** h - value)
        return value, error

    @staticmethod
    def my_wrapper(evaluator, value_dict):
        try:
            result, error = evaluator._compiled_code(*(value_dict[x] for x in evaluator._vars))
            int_result = int(result)
            if result == int_result > 0:
                return MyString(str(int_result), error),
            return ()
        except ArithmeticError:
            return ()

    def get_letter_values(self, known_letters: KnownLetterDict, letters: Sequence[str]) -> Iterable[Sequence[int]]:
        if not letters:
            return [()]
        unused_values = {i for i in self._items if i not in set(known_letters.values())}
        length = len(letters)

        def recurse(index) -> Iterable[Sequence[int]]:
            unused_large_values = [i for i in unused_values if i > 5]
            if all(letters[i] not in self.exponents for i in range(index, length)):
                yield from itertools.permutations(unused_large_values, length - index)
                return
            first_letter_values = [i for i in unused_values if i <= 5] if letters[index] in self.exponents else unused_large_values
            if index + 1 == length:
                yield from [(i,) for i in first_letter_values]
            else:
                for first_letter_value in first_letter_values:
                    unused_values.remove(first_letter_value)
                    for suffix in recurse(index + 1):
                        yield first_letter_value, *suffix
                    unused_values.add(first_letter_value)

        return recurse(0)

    def plot_board(self, clue_values=None, known_letters=None, **more_args) -> None:
        int_to_value = {value: letter for letter, value in known_letters.items()}
        if clue_values:
            clue_values = clue_values.copy()
            letters = ''.join(int_to_value[clue_values[clue].delta] for clue in self.clue_extras)
            clue_values[self.fake_clues[0]] = letters[0:10]
            clue_values[self.fake_clues[1]] = letters[10:20]
            clue_values[self.fake_clues[2]] = letters[20:30][::-1]
            clue_values[self.fake_clues[3]] = letters[30:][::-1]
        super().plot_board(clue_values, font_multiplier=0.7, **more_args)

    def draw_grid(self, top_bars, left_bars, **args) -> None:
        left_bars -= {(1, 11), (11, 2)}
        top_bars -= {(11, 11)}
        super().draw_grid(top_bars=top_bars, left_bars=left_bars, **args)

    def clue_from_name(self, name):
        if name.endswith('dn') or name.endswith('ac'):
            clue = self.clue_named(name[:-1])
        else:
            try:
                clue = self.clue_named(name + 'a')
            except:
                clue = self.clue_named(name + 'd')
        return clue

if __name__ == '__main__':
    Listener4843.run()
