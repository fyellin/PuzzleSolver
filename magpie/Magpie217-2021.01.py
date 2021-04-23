import itertools
import re
from typing import Dict, Tuple, Set, Sequence, Any

from solver import EquationSolver, Evaluator, Clue

EQUATIONS = """
1 A – B + BOT                , ((ANY – O)(N + E))**2
2 R+ EEL                     , ((N + O)(O + N))**2
3 B+ (E + A)R(D + S)         , TH(ROE + S)
4 HI +TS                     , JU(N – I + OR)
5 T+ OO+N                    , YO(G+H+UR–T–S)
6 (A + Y + E)(A + Y + E)     , (ANNE)**4
7 B + O + OK                 , (K + EY)**2
8 QUA – R – K                , UNSHEAT – H + E + S
9 OVEN                       , KIBB(U + T)/Z
10 V(AG + R – A – N)T        , EXT(R + A + CT + I – N)G
11 BA(T + H – E + R)         , EVE(R + Y + T(H – I) + N + G)
12 P(A + N)G                 , BI(SH + O + P – S)
13 (F + E)(L – I + NE)       , S(H – AD)OW
14 T + OW                    , UP(– A + G + U – M)(T + RE) – E
15 J(AD – E + D)             , E((N – U + M + E)R + A)TES
16 PET                       , K(NE – E – S + OC)K
"""


class Magpie217 (EquationSolver):
    graph: Dict[str, Set[str]]

    @staticmethod
    def run() -> None:
        solver = Magpie217()
        solver.solve(debug=True, max_debug_depth=50)

    def __init__(self) -> None:
        self.graph = self.get_graph()
        super().__init__(self.get_clue_list(), items=range(1, 27))

    def get_clue_list(self) -> Sequence[Clue]:
        equations = self.read_equations()
        clues = []
        for i in range(16):
            equation1, equation2 = equations[i + 1]
            rr = 2 * (i // 4) + 2
            cc = 2 * (i % 4) + 2
            locations = [(rr, cc), (rr - 1, cc - 1), (rr - 1, cc), (rr - 1, cc + 1), (rr, cc + 1), (rr + 1, cc + 1),
                         (rr + 1, cc), (rr + 1, cc - 1), (rr, cc - 1)]
            evaluator1 = Clue.create_evaluator(equation1, globals())
            evaluator2 = Clue.create_evaluator(equation2, globals())

            clue = Clue(str(i + 1), True, (rr, cc), 9, expression=f'{equation1} + {equation2}',
                        locations=locations, context=(evaluator1, evaluator2))
            clues.append(clue)
        return clues


    def evaluate(self, clue, evaluator: Evaluator) -> Sequence[str]:
        ev1, ev2 = clue.context
        v1 = ev1(self._known_letters)
        if v1 not in self.graph:
            return []
        v2 = ev2(self._known_letters)
        if v2 not in self.graph[v1]:
            return []
        digits = v1 + v2
        missing = next(x for x in '123456789' if x not in digits)
        return [missing + digits[i:] + digits[:i] for i in range(8)]

    def draw_grid(self, **args: Any) -> None:
        left_bars = []
        top_bars = []
        shading = {}
        for rr, cc in itertools.product((2, 4, 6, 8), repeat=2):
            left_bars.extend([(rr, cc), (rr, cc + 1)])
            top_bars.extend([(rr, cc), (rr + 1, cc)])
            shading[rr, cc] = 'lightblue'
        args['top_bars'] = top_bars
        args['left_bars'] = left_bars
        args['shading'] = shading
        super().draw_grid(**args)

    @staticmethod
    def get_graph() -> Dict[str, Set[str]]:
        result = {}
        digits = set("123456789")
        for a, b, c in itertools.combinations('123456789', 3):
            others = digits.difference([a, b, c])
            values = {''.join(x) for x in itertools.permutations(others, 5)}
            for x, y, z in itertools.permutations((a, b, c)):
                result[x + y + z] = values
        return result

    @staticmethod
    def read_equations() -> Dict[int, Tuple[str, str]]:
        result = {}
        lines = EQUATIONS.splitlines()
        lines = [line for line in lines if line]
        for line in lines:
            match = re.fullmatch(r'(\d+) ([^,]*), ([^,]*)', line)
            result[int(match.group(1))] = match.group(2, 3)
        return result


if __name__ == '__main__':
    Magpie217.run()
