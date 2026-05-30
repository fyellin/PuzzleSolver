import string
from collections.abc import Iterable, Sequence

from solver import (
    Clue,
    Clues,
    EquationParser,
    EquationSolver,
    Evaluator,
    KnownClueDict,
    KnownLetterDict,
)

ACROSS_LENGTHS = "232/133/2122/232/2212/331/232"
DOWN_LENGTHS = "322/421/133/232/331/124/223"

ACROSS = """
 1  T(W+O)-PR+OP-E+R+BE+A+TS
 3  TOO+LS+S+H+ED+S
 6  MO+RPH-A-L+T-E+R
 8  M+O/(THE)+R+LO+AD
10  PO+E+T+WRO+TE
12  OTH+ER
13  BR-E+A+THE
14  A+L+L-OW+S
16  P+O+WE+R-T+O+BE-ME
19  RO+LE-MO-D-E+LS
20  W+E+(B+O+T+H-E)R
22  B-E+BO-L+D
23  WOE+T-A+L+E
25  P+ROM-O-TE-TH+E+BE(S+T)
26  T^(HE)
27  O-T+HER-B+RO-T-(H+E)R
28  (W+H+E)EL
29  (B+E)HE(R+E)
"""

DOWN = """
 1  PLATE-O-R+B+(O+W)L+S
 2  WATER+S+PORTS+T(H-E+R)+E
 4  LE-T-T+H-EM+(H+A)TE
 5  D-R+AW+SW+ORD+S
 7  MMM+M
 9  BLA+M-E-(O-T+H-E)RS
11  B+E-LL+T-O+W-E-R
13  L(O+S)E+TE+MP-E+R
15  T+H-E-LA+ST+WO-RD
16  T-HE+(E+A)R-TH
18  (W+O+R+L)D+MAPS
19  BE+L+OW-A+(L+A)DDER
21  W-(H+E)W
22  BOB
24  E+MBED+S(O-ME)-M-ORALS
25  DR+EAM+S
26  T+O+B-E+S(T-A-B-L+E)+W-H+O-L+E
"""
# A  B  D  E  H  L  M  O  P  R  S  T  W
# 3  11 8  2  1  12 7  6  9  5  4  10 13


class Magpie281(EquationSolver):
    @classmethod
    def run(cls):
        cls.run2()

    @classmethod
    def run2(cls) -> None:
        solver = cls()
        solver.solve(debug=False, max_debug_depth=2)

    def __init__(self) -> None:
        clues = self.get_clues()
        super().__init__(clues, items=range(1, 14))

    def get_clues(self) -> Sequence[Clue]:
        clues = Clues.create_from_text2(ACROSS, DOWN, ACROSS_LENGTHS, DOWN_LENGTHS,
                                        create_unmatched_clues=True)
        for clue in clues:
            if not clue.evaluators:
                continue
            variables = clue.evaluators[0].vars
            info = tuple((index, expression,
                          Evaluator.create_evaluator(
                              expression, outer_vars=variables, lambda_name=f'{clue.name}-{index}'))
                         for expression, index in self.get_expression_alternatives(clue))
            clue.extra_info = info
            clue.evaluators[0].variables = variables
            clue.evaluators[0].extra_info = info
            clue.evaluators[0].set_wrapper(self.my_wrapper)
        return clues

    @staticmethod
    def my_wrapper(evaluator: Evaluator, value_dict: dict[str, int]) -> Iterable[str]:
        seen = set()
        values = [value_dict[x] for x in evaluator.variables]
        for _, _, ev2 in evaluator.extra_info:
            try:
                result = ev2.compiled_code(*values)
                int_result = int(result)
                if result == int_result > 0 and result not in seen:
                    seen.add(result)
                    yield str(int_result)
            except ArithmeticError:
                pass

    def get_expression_alternatives(self, clue):
        parser = EquationParser()
        expression = clue.expression
        results = []
        seen = set()
        for i in range(len(expression)):
            if expression[i] not in string.ascii_letters:
                continue
            expression2 = expression[:i] + expression[i + 1:]
            if expression2 in seen:
                continue
            seen.add(expression2)
            try:
                result, = parser.parse(expression2)
            except SyntaxError:
                continue
            output = result.to_string(functions={'pos', 'neg'})
            if 'pos' in output or 'neg' in output:
                continue
            results.append((expression2, i))
        if clue.name == '26a':
            results.append(('HE', 0))
        return results

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        # super().show_solution(known_clues, known_letters)
        clues = sorted(self.clue_list, key=lambda clue: (not clue.is_across, clue.base_location))
        end_result = []
        for clue in clues:
            letters = set()
            if not clue.evaluators:
                continue
            known_value = known_clues[clue]
            for index, _, evaluator in clue.extra_info:
                results = evaluator(known_letters)
                for result in results:
                    if result == known_value:
                        letters.add(clue.expression[index])
            assert len(letters) == 1
            end_result.append(letters.pop())
        message = ''.join(end_result)
        message = message[0:18] + "\n" + message[18:]
        super().show_solution(known_clues, known_letters,
                              # subtext="RUDYARD LAKE",
                              subtext=message
                              )


if __name__ == '__main__':
    Magpie281.run()
