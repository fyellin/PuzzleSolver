from collections import Counter, defaultdict
from collections.abc import Sequence
from datetime import datetime
from itertools import permutations

from solver import Clue, Clues, DancingLinks, Encoder, EquationSolver

GRID = """
XXXXXXXX
X.X...X.
XX..X.X.
X...X...
X.XXXX..
X...X..X
XXX...X.
X....X..
"""

ACROSSES = """
1 MEW (3) 
6 MET (3)
9 S + AW (2)
10 C + (OC)**O – NU + T (4)
11 U(T + E)                        (2)
12 COME                            (4)
14 UN(C + O)(M + M**O + N)   (4)
16 TO(A + S + T)                   (4)
17 C**O + N + M – E + N              (4)
18 S + T**O + N + E + M + A + S + ON (4)
21 (C – O)MM(ENCE + M – E + N + T) (4)
23 (S + T – UN)(T + W – O)(M**E - N) (4)
24 (N + U + A)(N + C + E + S!)     (4)
26 OUT                             (2)
28 (C + O)**U   + S – (C + O)**(U – S!)  (4)
29 WA + N + T + O + N + S!         (2)
30 (C + O + A)T                    (3)
31 C(A + M + E)                    (3)
"""

DOWNS = """
1 AT (3) 
2 C + A + W (2) 
3 (U – N)C(O + M)(M + O) – N (4) 
4 ST + A + TEME + N + T (4) 
5 (M + U)**(O + N) – (M + E)(S + O + N) (4) 
6 MONUMEN – T (4) 
7 C(O + N) (2) 
8 W**(O + N) – T(O – N) (3)
13 M + ANATE – E (4) 
15 ATTE – N – U – A + T – E (4) 
19 (A + U)T – O + C + U**E (4) 
20 (C + O)M(M + A) (4) 
21 M**ET – M + A – N (4) 
22 (M**E – N)(A – C + E – S!) (4) 
23 (C + O – N + S + U)**M + E (3) 
25 M**A (3) 
27 NONCOM + S – M (2) 
29 A(M + E) + N (2)
"""


class Magpie252 (EquationSolver):
    @staticmethod
    def run():
        solver = Magpie252()
        solver.verify_is_180_symmetric()
        results = solver.step1_mp()
        assert len(results) == 1
        vars, values = results[0]
        solver.step2(vars, values)

    def __init__(self) -> None:
        self.vars = ('A', 'C', 'E', 'M', 'N', 'O', 'S', 'T', 'U', 'W')
        self.deltas = (0, 3, 4, 5, 9, 10, 10, 10, 12, 15, 15, 16, 18, 18, 20, 25, 25, 27,
                       36, 43, 44, 51, 52, 122, 134, 210, 248, 316, 534, 602, 638, 720)
        self.ok_values = self.get_ok_values()
        clues = self.get_clues()
        super().__init__(clues)

    def get_clues(self) -> Sequence[Clue]:
        grid = Clues.get_locations_from_grid(GRID)
        clues = Clues.create_from_text(ACROSSES, DOWNS, grid)
        for clue in clues:
            clue.evaluators[0].set_wrapper(self.my_wrapper)
        return clues

    @staticmethod
    def my_wrapper(evaluator, value_dict: dict[str, int]) -> int:
        result = evaluator._compiled_code(*(value_dict[x] for x in evaluator._vars))
        int_result = int(result)
        if result == int_result > 0:
            return result
        raise ArithmeticError

    def get_ok_values(self):
        result = defaultdict(list)
        deltas = self.deltas
        for x in range(2, 100):
            for delta in set(deltas):
                y = x + delta
                if 10 <= x * y <= 9999:
                    result[2 * (2 * x + y - 1)].append((x*y, x, y, delta))
                    if delta != 0:
                        result[2 * (2 * y + x - 1)].append((x*y, y, x, delta))
        return result

    def step1_old(self):
        clues = self._clue_list
        evaluators = [clue.evaluators[0] for clue in clues]
        time1 = datetime.now()
        for count, values in enumerate(permutations(range(10))):
            my_dict = dict(zip(self.vars, values))
            try:
                results = [evaluator(my_dict) for evaluator in evaluators]
                xresults = [r for r in results if r not in self.ok_values]
                if len(xresults) > 4:
                    continue
                print(values, results)
            except ArithmeticError:
                pass
        time2 = datetime.now()
        print(time2 - time1)

    @staticmethod
    def initialize_mp():
        global mp_solver
        solver = Magpie252()
        clues = solver._clue_list
        solver.evaluators = [clue.evaluators[0] for clue in clues]
        mp_solver = solver

    @staticmethod
    def run_one_permutation(values):
        solver = mp_solver
        my_dict = dict(zip(solver.vars, values))
        try:
            results = [evaluator(my_dict) for evaluator in solver.evaluators]
            xresults = [r for r in results if r not in solver.ok_values]
            if len(xresults) <= 4:
                return values, results
        except ArithmeticError:
            pass
        return None

    def step1_mp(self):
        import multiprocessing as mp
        time1 = datetime.now()
        results = []
        with mp.Pool(initializer=self.initialize_mp) as pool:
            for result in pool.imap_unordered(self.run_one_permutation,
                                              permutations(range(10)), chunksize=1_000):
                if result:
                    results.append(result)
        time2 = datetime.now()
        print(time2 - time1)
        return results

    VALUES = (9, 7, 5, 2, 1, 3, 0, 8, 4, 6)
    RESULTS = (60, 80, 54, 9272, 52, 210, 440, 408, 342, 532, 2896, 1364, 196, 96,
               9000, 68, 152, 112, 72, 22, 524, 418, 1268, 232, 28, 1280, 3237, 2869,
               1132, 220, 262, 186, 174, 512, 124, 64)

    def step2(self, values=VALUES, results=RESULTS):
        encoder = Encoder.digits()
        counter = Counter(self.deltas)
        # self.show_letter_values(dict(zip(self.vars, values)))

        double_delta_clues = defaultdict(set)
        for clue, result in zip(self._clue_list, results):
            for xy, x, y, delta in self.ok_values[result]:
                if counter[delta] > 1:
                    double_delta_clues[delta].add(clue)

        constraints = {}
        optional_constraints = {f'X-{clue.name}-{delta}-{f}'
                                for delta, clues in double_delta_clues.items()
                                for clue in clues
                                for f in range(counter[delta])}

        for clue_index, (clue, result) in enumerate(zip(self._clue_list, results)):
            if self.ok_values[result]:
                for xy, x, y, delta in self.ok_values[result]:
                    if len(str(xy)) == clue.length:
                        for f in range(counter[delta]):
                            row = [f'C-{clue.name}', f'D{delta}-{f}']
                            row.extend(item for location, digit in zip(clue.locations, str(xy))
                                       if self.is_intersection(location)
                                       for item in encoder.encode(digit, location, clue.is_across))
                            if delta in double_delta_clues:
                                row.append(f'X-{clue.name}-{delta}-{f}')
                                if f > 0:
                                    row.extend(f'X-{clue2.name}-{delta}-{f - 1}'
                                               for clue2 in self._clue_list[clue_index + 1:]
                                               if clue2 in double_delta_clues[delta])
                            constraints[clue.name, xy, x, y, f] = row
            else:
                assert len(str(result)) == clue.length
                row = [f'C-{clue.name}']
                for location, digit in zip(clue.locations, str(result)):
                    if self.is_intersection(location):
                        row.extend(encoder.encode(digit, location, clue.is_across))
                constraints[clue.name, result, 0, 0, 0] = row

        def my_row_printer(solution):
            clue_values = {self.clue_named(name): str(value) for name, value, *_ in solution}
            self.plot_board(clue_values, values=values)

        solver = DancingLinks(constraints, optional_constraints=optional_constraints,
                              row_printer=my_row_printer)
        solver.solve(debug=False)

    def draw_grid(self, location_to_entry, values, **args) -> None:
        number_to_letter = {str(digit): var for var, digit in zip(self.vars, values)}
        for x, y in ((1, 2), (2, 1), (3, 3), (4, 4)):
            for location in ((x, y), (9 - y, x), (9 - x, 9 - y), (y, 9 - x)):
                old = location_to_entry[location]
                location_to_entry[location] = number_to_letter[old]
        rotation = {(5, 4): 90}
        super().draw_grid(location_to_entry=location_to_entry,
                          font_multiplier=.75,
                          rotation=rotation,
                          **args)


if __name__ == '__main__':
    Magpie252.run()
