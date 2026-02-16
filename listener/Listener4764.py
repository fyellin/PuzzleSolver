from collections import defaultdict
from itertools import permutations

from solver import Clue, ConstraintSolver, EquationSolver, KnownClueDict, EquationParser


def get_bcef_g_list():
    result = defaultdict(list)
    for b, c, e, f in permutations((1, 2, 3, 4, 5, 6, 7, 8, 9), 4):
        temp = b * e + 66 * c * f
        if 1000 <= temp <= 9999:
            bb, cc, ee, ff = list(str(temp))
            if len({bb, cc, ee, ff}) == 4 and '0' not in {bb, cc, ee, ff}:
                bcef = f'{b}{c}{e}{f}'
                g = f'{temp}'
                result[bcef].append((g, True))
                result[g].append((bcef, False))
    return result

CLUES = """
b −D + UR**(A + T) + I + ON**S
i R + O(TU + N)DA
k (S + I +T**A + RO − U − N)D
n U((N + I)**T − (A + R)D)S
o (A + S)T(R**O − √(ID))
p SU**T + (O + R + I)A + N
s (DI − NO)(S + T)A + R
v (T/R)I**N(ODU + S)
w (TU**N(D + R) + A)S
y −(√I)N + TRADO + S
c −D + U(R + A)(T**I + ON**S )
d DI(N**OS + A + U)R
e (AROU + N)D
f A(U + D) + (I + T + O)R**S
j S − A + U**T(O + I − R)
m (S(U + D − A) − T)IO + N
q R − (A + I + N + O − U**T)S
r ((N + U)**T + RI + S + O + D)A
t R(O(√D − A + UST) − I + N)
u A(S**T + OU + N) + D
"""

class Listener4764(ConstraintSolver):
    @staticmethod
    def run():
        solver = Listener4764()
        solver.solve()

    def __init__(self):
        self.good_list = get_bcef_g_list()
        clues = self.get_clues()
        self.real_clues = clues[:-4]
        super().__init__(clues)

    def solve(self):
        dictionary = self.get_letter_values()
        self.dictionary = dictionary
        for clue in self._clue_list:
            clue.generator = self.generator
            if clue.length == 4:
                value = clue.evaluators[0](dictionary)[0]
                clue.context = value
        super().solve(debug=False)

    def generator(self, clue):
        if clue.length == 8:
            for value1, pairs in self.good_list.items():
                for value2, is_good in pairs:
                    if is_good:
                        yield value1 + value2
        else:
            value = clue.context
            yield from (x for x, y in self.good_list[value])

    def check_solution(self, known_clues: KnownClueDict) -> bool:
        count1 = count2 = 0
        for clue in self.real_clues:
            actual = clue.context
            entered = known_clues[clue]
            count1 += (entered, True) in self.good_list[actual]
            count2 += (entered, False) in self.good_list[actual]
        assert count1 >= 7 and count2 >= 13
        return len(set(known_clues[self.clue_named('a')])) == 8

    def show_solution(self, known_clues: KnownClueDict) -> None:
        possibilities = list(self.generator(self.clue_named('a')))
        seen = {known_clues[self.clue_named(name)][4:] for name in 'aghx'}
        possibilities = [x for x in possibilities if len(set(x)) == 8 and x[4:] not in seen]
        alt_dict = {str(value): letter for letter, value in self.dictionary.items()}
        result = min(possibilities)
        result = ''.join(alt_dict[i] for i in result)
        result = result[:4] + ' ' + result[4:]
        self.show_off(known_clues)
        self.plot_board(known_clues, subtext=''.join(result),
                        blacken_unused=False, file="/tmp/stuff.jpg")
        EquationSolver(self._clue_list).show_letter_values(self.get_letter_values())

    def get_clues(self):
        locations = dict(a=(1,2), b=(1,3), c=(1,3), d=(1,4), e=(1,5), f=(1,6), g=(1,7),
                         h=(2,1), i=(3,1), j=(3,1), k=(3,5), m=(3,8), n=(4,1), o=(4,5),
                         p=(5,1), q=(5,3), r=(5,4), s=(5,5), t=(5,5), u=(5,6), v=(6,1),
                         w=(6,5), x=(7,1), y=(8,3))
        clues = []
        for line in CLUES.strip().splitlines():
            line = line.strip()
            letter, expression = line[0], line[2:]
            is_across = letter in "biknopsvwy"
            clue = Clue(letter, is_across, locations[letter], 4, expression=expression)
            clues.append(clue)
        for letter in 'aghx':
            clue = Clue(letter, letter in 'hx', locations[letter], 8)
            clues.append(clue)
        return clues

    def get_letter_values(self, fast=True):
        if fast:
            return {'D': 9, 'U': 6, 'R': 2, 'A': 5, 'T': 3, 'I': 4, 'O': 7, 'N': 1, 'S': 8}

        dictionaries = [dict(zip(list('DURATIONS'), permutation))
                        for permutation in permutations(range(1, 10))]
        for clue in self.real_clues:
            evaluator = clue.evaluators[0]
            dictionaries = [dictionary for dictionary in dictionaries
                            for results in [evaluator(dictionary)]
                            if len(results) == 1 and results[0] in self.good_list]
        assert len(dictionaries) == 1
        return dictionaries[0]

    def show_off(self, known_clues):
        import math
        letter_values = self.get_letter_values(True).copy()
        letter_values['sqrt'] = math.sqrt
        eq = EquationParser()

        for clue in self.real_clues:
            value1 = clue.evaluators[0](letter_values)[0]
            expression = eq.parse(clue.expression)[0].to_string(simple=True)
            value2 = eval(expression, letter_values)
            assert str(int(value2)) == value1
            entry = known_clues[clue]
            is_forward = next(is_forward for value, is_forward in self.good_list[value1] if value == entry)
            code = '<<--' if is_forward else '-->>'
            print(f'{clue.name} = {entry} {code} {value1} = {expression}')


if __name__ == '__main__':
    Listener4764.run()
