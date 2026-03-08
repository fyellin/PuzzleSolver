from solver import Clues, DancingLinks, DLConstraint, EquationSolver
from solver.helpers import digit_product as DP
from solver.helpers import digit_sum as DS


def possibilities(digits, is_across):
    sub_func, add_func = (DS, DP) if is_across else (DP, DS)
    min_value, max_value = 10 ** (digits - 1), 10 ** digits
    result = []
    for low in range(min_value, max_value):
        if '0' in str(low):
            continue
        addend = add_func(low)
        for start in range(low, max_value - addend):
            high = start + addend
            if low == start - sub_func(high) and '0' not in str(high):
                result.append((low, high, start))
    return result


class Magpie268 (EquationSolver):
    @classmethod
    def run(cls):
        solver = cls()
        solver.verify_is_180_symmetric()
        solver.solve()

    def __init__(self) -> None:
        clues = Clues.clues_from_clue_sizes("22/31/13/22", "22/13/31/22")
        super().__init__(clues)

    def solve(self, **args):
        constraints = {}
        optional = {f'r{r}c{c}' for r in range(1, 5) for c in range(1, 5)}
        across_pairs = ((1, 10), (2, 9), (4, 7))
        down_pairs = ((1, 8), (2, 5), (3, 6))

        for is_across in (True, False):
            if is_across:
                tag, pairs = 'a', across_pairs
            else:
                tag, pairs = 'd', down_pairs
            for pair in pairs:
                clues = tuple(self.clue_named(f'{num}{tag}') for num in pair)
                clue1, clue2 = clues
                assert clue1.length == clue2.length
                triples = possibilities(clues[0].length, is_across)
                if is_across and clue1.length == 3:
                    triples = [triple for triple in triples if triple[2] == 496]
                for (low, high, start) in triples:
                    # We don't know which clue gets the low value and which gets the high
                    for values in ((low, high), (high, low)):
                        # Include low, high, value since they are supposed to be unique
                        constraint: list[DLConstraint] = [
                            clue1.name, clue2.name, str(low), str(high), str(start)]
                        optional.update(constraint[2:])
                        # Add to the constraint that clue1 = value1 and clue2 = value2
                        for clue, value in zip(clues, values):
                            constraint.extend(clue.dancing_links_rc_constraints(value))
                        if str(start) == str(start)[::-1]:
                            # There is to be one "start" value that's a palindrome.
                            constraint.append('palindrome')
                        constraints[tuple(zip(clues, values))] = constraint

        def row_printer(result):
            solution = {clue: str(value)
                        for pairs in result for (clue, value) in pairs}
            print(solution)
            self.plot_board(solution)

        solver = DancingLinks(constraints, optional_constraints=optional,
                              row_printer=row_printer)
        solver.solve(debug=100)


if __name__ == '__main__':
    Magpie268.run()
