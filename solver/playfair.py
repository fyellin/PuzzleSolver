from typing import Sequence, List, Optional, Mapping

from .playfair_constraints import ConstraintsGenerator, ConstraintRow


class PlayfairSolver(object):
    results: List[ConstraintRow]
    debug: bool
    count: int

    @staticmethod
    def test(*, debug: bool = False) -> None:
        solver = PlayfairSolver(
            plain_text='TOPSYTURVY' 'INVERTED' 'UPSIDEDOWN',
            cipher_text='WK..A.YVRU' 'SMI..HFE' 'PBWSEF..SO',
            tail=12)
        results = solver.solve(debug=debug)
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
            return row.fill_in_tail(self.sortedTailLength)

        constraints = self.constraints_generator.generate_all_constraints()
        constraints = {name: list(filter(None, map(filler, constraint_rows)))
                       for name, constraint_rows in constraints.items()}
        self.count = 0
        self.debug = debug
        self.__solve(0, constraints, ConstraintRow.empty())
        return self.results

    def __solve(self, depth: int,
                pending_constraints: Mapping[str, Sequence[ConstraintRow]],
                rows_so_far: ConstraintRow) -> None:
        self.count += 1
        indent = " | " * depth if self.debug else None
        if not pending_constraints:
            if self.debug:
                print("{}✓ SOLUTION = {}".format(indent, rows_so_far))
            self.results.append(rows_so_far)
            return
        # Determine which constraint has the fewest rows in it
        min_constraint_name, min_constraint = min(pending_constraints.items(), key=lambda x: (len(x[1]), x[0]))
        min_count = len(min_constraint)
        if min_count == 0:
            if self.debug:
                print(f"{indent}✕ {min_constraint_name}")
            return

        for i, current_row in enumerate(min_constraint):
            next_rows_so_far_direct = rows_so_far + current_row
            next_rows_so_far = next_rows_so_far_direct.fill_in_tail(self.sortedTailLength)
            if not next_rows_so_far:
                if self.debug:
                    print("{}{}/{}✕ \"{}\" {} -> {}:".format(
                        indent, i + 1, min_count, min_constraint_name, current_row, next_rows_so_far_direct))
                continue
            # For the recursive call, only keep those rows that are consistent with what we have built up so far.
            # We also remove the current constraint from the table.
            next_pending_constraints = {name: [row for row in constraint if row.is_consistent_with(next_rows_so_far)]
                                        for name, constraint in pending_constraints.items()
                                        if name != min_constraint_name}
            if self.debug:
                sizes = [f"{name}: {len(pending_constraints[name])}->{len(next_pending_constraints[name])}"
                         for name in sorted(next_pending_constraints.keys())
                         if len(pending_constraints[name]) != len(next_pending_constraints[name])]
                if next_rows_so_far_direct != next_rows_so_far:
                    temp = f"{next_rows_so_far} -> {next_rows_so_far_direct}"
                else:
                    temp = f"{next_rows_so_far}"
                if min_count == 1:
                    # If this item was forced, we format it a little bit differently, and don't increase the indent.
                    print(f"{indent}• \"{min_constraint_name}\" {current_row} -> {temp} : {sizes}")
                else:
                    print(f"{indent}{i + 1}/{min_count} \"{min_constraint_name}\" {current_row} -> {temp} : {sizes}")

            self.__solve(depth + 1 if min_count > 1 else depth, next_pending_constraints, next_rows_so_far)
