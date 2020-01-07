from typing import Sequence, List, Optional, Mapping

from .playfair_constraints import ConstraintsGenerator, ConstraintRow


class PlayfairSolver(object):
    results: List[ConstraintRow]
    debug: bool
    count: int

    @staticmethod
    def test() -> None:
        solver = PlayfairSolver(
            plain_text='TOPSYTURVY' 'INVERTED' 'UPSIDEDOWN',
            cipher_text='WK..A.YVRU' 'SMI..HFE' 'PBWSEF..SO',
            tail=11)
        results = solver.solve()
        for result in results:
            missing = ''.join(sorted(result.missing_letters()))
            print(result, missing)

    def __init__(self, plain_text: str, cipher_text: str, tail: int = 11):
        self.results = []
        # cipher_text = cipher_text.replace("M", ".").replace("W", ".")
        # plain_text = plain_text.replace("M", ".").replace("W", ".")
        self.sortedTailLength = tail
        self.constraints_generator = ConstraintsGenerator(plain_text, cipher_text)

    def solve(self, *, debug: bool = False) -> Sequence[ConstraintRow]:

        def filler(row: ConstraintRow) -> Optional[ConstraintRow]:
            return row.check_tail_and_fill_in_as_able(self.sortedTailLength)

        constraints = self.constraints_generator.generate_all_constraints()
        constraints = {name: list(filter(None, map(filler, constraint_rows)))
                       for name, constraint_rows in constraints.items()}
        self.count = 0
        self.debug = debug
        self.run_inner(0, constraints, ConstraintRow.empty())
        return self.results

    def run_inner(self, depth: int,
                  pending_constraints_table: Mapping[str, Sequence[ConstraintRow]],
                  rows_so_far: ConstraintRow) -> None:
        self.count += 1
        indent = " | " * depth if self.debug else None
        if not pending_constraints_table:
            if self.debug:
                print("{}✓ SOLUTION = {}".format(indent, rows_so_far))
            self.results.append(rows_so_far)
            return
        # Determine which constraint has the fewest rows in it
        min_count, min_constraint_name = min(
            [(len(constraint_rows), name) for name, constraint_rows in pending_constraints_table.items()])
        min_constraint = pending_constraints_table[min_constraint_name]
        if min_count == 0:
            if self.debug:
                print("{}✕ {}".format(indent, min_constraint_name))
            return

        for i, current_row in enumerate(min_constraint):
            next_rows_so_far_direct = rows_so_far + current_row
            next_rows_so_far = next_rows_so_far_direct.check_tail_and_fill_in_as_able(self.sortedTailLength)
            if not next_rows_so_far:
                if self.debug:
                    print("{}{}/{}✕ \"{}\" {} -> {}:".format(
                        indent, i + 1, min_count, min_constraint_name, current_row, next_rows_so_far_direct))
                continue
            # For the recursive call, only keep those rows that are consistent with what we have built up so far.
            # We also remove the current constraint from the table.
            next_constraints_table = {name: [row for row in constraint if row.is_consistent_with(next_rows_so_far)]
                                      for name, constraint in pending_constraints_table.items()
                                      if name != min_constraint_name}
            if self.debug:
                sizes = [(name, len(pending_constraints_table[name]), len(next_constraints_table[name]))
                         for name in sorted(next_constraints_table.keys())]
                if next_rows_so_far_direct != next_rows_so_far:
                    temp = "{} -> {}".format(next_rows_so_far_direct, next_rows_so_far)
                else:
                    temp = "{}".format(next_rows_so_far)
                if min_count == 1:
                    # If this item was forced, we format it a little bit differently, and don't increase the indent.
                    print("{}• \"{}\" {} -> {} : {}".format(
                        indent, min_constraint_name, current_row, temp, sizes))
                else:
                    print("{}{}/{} \"{}\" {} -> {} : {}".format(
                        indent, i + 1, min_count, min_constraint_name, current_row, temp, sizes))

            self.run_inner(depth + 1 if min_count > 1 else depth, next_constraints_table, next_rows_so_far)
