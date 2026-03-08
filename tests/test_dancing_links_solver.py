"""Tests for DancingLinksSolver."""

from __future__ import annotations

from solver import Clue, DancingLinksSolver, KnownClueDict


def make_2x2_clues():
    """
    2x2 grid — four clues sharing every cell:
        (1,1)(1,2)
        (2,1)(2,2)
    1a: row 1 across   1d: col 1 down
    2a: row 2 across   2d: col 2 down
    """
    def gen(*values):
        return lambda clue: values

    clue_1a = Clue('1a', True,  (1, 1), 2, generator=gen('12', '34', '56', '78'))
    clue_2a = Clue('2a', True,  (2, 1), 2, generator=gen('12', '34', '56', '78'))
    clue_1d = Clue('1d', False, (1, 1), 2, generator=gen('13', '24', '57', '68'))
    clue_2d = Clue('2d', False, (1, 2), 2, generator=gen('13', '24', '57', '68'))
    return [clue_1a, clue_2a, clue_1d, clue_2d]


def collect_solutions(solver: DancingLinksSolver) -> list[dict[str, str]]:
    solutions: list[dict[str, str]] = []

    def capture(known_clues: KnownClueDict) -> None:
        solutions.append({clue.name: str(v) for clue, v in known_clues.items()})

    solver.show_solution = capture
    solver.solve(show_time=False)
    return solutions


def test_basic_two_solutions():
    # Grid must satisfy intersections: 1a[0]==1d[0], 1a[1]==2d[0], 2a[0]==1d[1], 2a[1]==2d[1]
    # Two consistent assignments exist:
    #   1a='12', 1d='13', 2d='24', 2a='34'  (col1: 1,3  col2: 2,4)
    #   1a='56', 1d='57', 2d='68', 2a='78'  (col1: 5,7  col2: 6,8)
    solver = DancingLinksSolver(make_2x2_clues())
    solutions = collect_solutions(solver)
    assert len(solutions) == 2
    by_1a = {s['1a']: s for s in solutions}
    assert by_1a['12'] == {'1a': '12', '2a': '34', '1d': '13', '2d': '24'}
    assert by_1a['56'] == {'1a': '56', '2a': '78', '1d': '57', '2d': '68'}


def test_singleton_constraint_filters_candidates():
    # Require 1a to be even (last digit even) — eliminates '12' (even ✓) vs '56' (even ✓)
    # Actually filter to only values whose first digit > 4, keeping only the '56' family.
    solver = DancingLinksSolver(make_2x2_clues(), allow_duplicates=False)
    solver.add_constraint('1a', lambda v: int(v[0]) > 4)
    solutions = collect_solutions(solver)
    assert len(solutions) == 1
    assert solutions[0]['1a'] == '56'


def test_multi_constraint_filters_solutions():
    # Add a cross-clue constraint: int(1a) + int(2a) < 100
    # 12 + 34 = 46 < 100 ✓  ;  56 + 78 = 134 ≥ 100 ✗
    solver = DancingLinksSolver(make_2x2_clues(), allow_duplicates=False)
    solver.add_constraint('1a 2a', lambda a, b: int(a) + int(b) < 100)
    solutions = collect_solutions(solver)
    assert len(solutions) == 1
    assert solutions[0]['1a'] == '12'


def test_no_duplicates_enforced():
    # 2x2 grid where one assignment has all four clues equal to '11'
    # (consistent at every intersection) and one has all distinct values.
    # With allow_duplicates=False the all-'11' solution must be rejected.
    def gen(*values):
        return lambda clue: values

    clue_1a = Clue('1a', True,  (1, 1), 2, generator=gen('11', '12'))
    clue_2a = Clue('2a', True,  (2, 1), 2, generator=gen('11', '34'))
    clue_1d = Clue('1d', False, (1, 1), 2, generator=gen('11', '13'))
    clue_2d = Clue('2d', False, (1, 2), 2, generator=gen('11', '24'))

    # With allow_duplicates=True both solutions are valid.
    solver_dup = DancingLinksSolver([clue_1a, clue_2a, clue_1d, clue_2d],
                                    allow_duplicates=True)
    all_solutions = collect_solutions(solver_dup)
    assert len(all_solutions) == 2

    # With allow_duplicates=False only the all-distinct solution survives.
    solver_nodup = DancingLinksSolver([clue_1a, clue_2a, clue_1d, clue_2d],
                                      allow_duplicates=False)
    solutions = collect_solutions(solver_nodup)
    assert len(solutions) == 1
    assert solutions[0] == {'1a': '12', '2a': '34', '1d': '13', '2d': '24'}


def test_update_constraints_adds_primary_column():
    # Override update_constraints to append a new primary column "force_12_family"
    # covered only by the (1a, '12') row.  Algorithm X must cover it, so 1a='12'
    # is forced and only that solution survives.
    class Solver(DancingLinksSolver):
        def update_constraints(self, constraints, optional_constraints, bounds):
            clue_1a = self.clue_named('1a')
            constraints[clue_1a, '12'].append('force_12_family')

    solver = Solver(make_2x2_clues())
    solutions = collect_solutions(solver)
    assert len(solutions) == 1
    assert solutions[0]['1a'] == '12'


def test_update_constraints_non_clue_rows_ignored():
    # Add a row with a plain-string key and a matching primary column.
    # DL must select it (only row covering that column), but on_solution
    # should not include it in known_clues.
    received: list[KnownClueDict] = []

    class Solver(DancingLinksSolver):
        def update_constraints(self, constraints, optional_constraints, bounds):
            constraints['auxiliary'] = ['aux_col']

        def show_solution(self, known_clues: KnownClueDict) -> None:
            received.append(known_clues)

    solver = Solver(make_2x2_clues())
    solver.solve(show_time=False)
    assert len(received) == 2
    for known_clues in received:
        assert all(isinstance(k, Clue) for k in known_clues)


def test_no_solution():
    # Generators that can never satisfy intersections.
    def gen(*values):
        return lambda clue: values

    clue_1a = Clue('1a', True,  (1, 1), 2, generator=gen('12'))
    clue_1d = Clue('1d', False, (1, 1), 2, generator=gen('34'))  # needs first digit '1', has '3'
    solver = DancingLinksSolver([clue_1a, clue_1d], allow_duplicates=False)
    solutions = collect_solutions(solver)
    assert solutions == []
