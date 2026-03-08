"""Tests for DancingLinksBounds (Algorithm M: exact cover with multiplicities and colors)."""
import pytest

from solver.dancing_links import DancingLinksBounds

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def collect_solutions(constraints, *, optional_constraints=None, bounds=None):
    """Run the solver and return a sorted list of frozensets (one per solution)."""
    solutions = []
    dl = DancingLinksBounds(
        constraints,
        row_printer=lambda rows: solutions.append(frozenset(rows)),
        optional_constraints=optional_constraints or set(),
        bounds=bounds or {},
    )
    dl.solve()
    assert len(solutions) == len(set(solutions)), "No solutions are produced more than once."
    return sorted(solutions)


# ---------------------------------------------------------------------------
# 1. Multiplicity: lo == hi > 1 (item must be covered exactly N times)
# ---------------------------------------------------------------------------


def test_exact_multiplicity_two():
    """Item A must be covered exactly twice; three rows cover it — C(3,2)=3 solutions."""
    constraints = {
        'r1': ['A'],
        'r2': ['A'],
        'r3': ['A'],
    }
    solutions = collect_solutions(constraints, bounds={'A': (2, 2)})
    assert len(solutions) == 3
    assert frozenset({'r1', 'r2'}) in solutions
    assert frozenset({'r1', 'r3'}) in solutions
    assert frozenset({'r2', 'r3'}) in solutions


def test_multiplicity_two_with_second_item():
    """A must be covered twice, B exactly once.

    r1 covers A+B; r2 and r3 cover only A.
    r1 must be chosen (only row covering B), plus exactly one of r2/r3.
    """
    constraints = {
        'r1': ['A', 'B'],
        'r2': ['A'],
        'r3': ['A'],
    }
    solutions = collect_solutions(constraints, bounds={'A': (2, 2)})
    assert len(solutions) == 2
    assert frozenset({'r1', 'r2'}) in solutions
    assert frozenset({'r1', 'r3'}) in solutions


def test_multiplicity_infeasible():
    """A must be covered twice but only one row exists — no solution."""
    constraints = {
        'r1': ['A'],
    }
    solutions = collect_solutions(constraints, bounds={'A': (2, 2)})
    assert solutions == []


# ---------------------------------------------------------------------------
# 2. Slack: lo < hi (item may be covered anywhere in [lo, hi] times)
# ---------------------------------------------------------------------------


def test_slack_optional_cover():
    """A must be covered 1-2 times, B exactly once.

    Rows: r1 covers A+B, r2 covers A only.
    Solutions: {r1} (A=1) and {r1, r2} (A=2).
    """
    constraints = {
        'r1': ['A', 'B'],
        'r2': ['A'],
    }
    solutions = collect_solutions(constraints, bounds={'A': (1, 2)})
    assert frozenset({'r1'}) in solutions
    assert frozenset({'r1', 'r2'}) in solutions
    assert len(solutions) == 2


def test_slack_zero_to_two():
    """A may be covered 0-2 times (fully optional primary), B exactly once.

    Rows: r1 covers B only, r2 covers A+B, r3 covers A.
    Solutions: {r1}, {r1, r3}, {r2}, {r2, r3}.
    """
    constraints = {
        'r1': ['B'],
        'r2': ['A', 'B'],
        'r3': ['A'],
    }

    solutions = collect_solutions(constraints, bounds={'A': (0, 2)})
    assert frozenset({'r1'}) in solutions
    assert frozenset({'r1', 'r3'}) in solutions
    assert frozenset({'r2'}) in solutions
    assert frozenset({'r2', 'r3'}) in solutions
    assert len(solutions) == 4


# ---------------------------------------------------------------------------
# 3. Colors and multiplicity combined
# ---------------------------------------------------------------------------


def test_colors_with_multiplicity():
    """Colors and multiplicity bounds work together.

    A must be covered twice; S is a secondary colored item.
    r1 covers A + S:red, r2 covers A + S:red, r3 covers A + S:blue.
    Solutions where A is covered twice and S colors agree: {r1,r2} only.
    """
    constraints = {
        'r1': ['A', ('S', 'red')],
        'r2': ['A', ('S', 'red')],
        'r3': ['A', ('S', 'blue')],
    }
    solutions = collect_solutions(
        constraints, optional_constraints={'S'}, bounds={'A': (2, 2)}
    )
    assert solutions == [frozenset({'r1', 'r2'})]


# ---------------------------------------------------------------------------
# 4. Higher multiplicity
# ---------------------------------------------------------------------------


def test_exact_multiplicity_three():
    """Item A must be covered exactly 3 times; four rows — C(4,3)=4 solutions."""
    constraints = {
        'r1': ['A'],
        'r2': ['A'],
        'r3': ['A'],
        'r4': ['A'],
    }
    solutions = collect_solutions(constraints, bounds={'A': (3, 3)})
    assert len(solutions) == 4
    assert frozenset({'r1', 'r2', 'r3'}) in solutions
    assert frozenset({'r1', 'r2', 'r4'}) in solutions
    assert frozenset({'r1', 'r3', 'r4'}) in solutions
    assert frozenset({'r2', 'r3', 'r4'}) in solutions


# ---------------------------------------------------------------------------
# 5. Non-uniform bounds across items
# ---------------------------------------------------------------------------


def test_non_uniform_bounds():
    """A must be covered twice, B exactly once; rows interact."""
    constraints = {
        'r1': ['A', 'B'],
        'r2': ['A'],
        'r3': ['A'],
        'r4': ['A', 'B'],
    }
    # Choosing r1 (covers A+B) forces B satisfied, need one more A from {r2,r3}.
    # Choosing r4 (covers A+B) same logic.
    # Can't pick both r1 and r4 — B would be covered twice.
    solutions = collect_solutions(constraints, bounds={'A': (2, 2)})
    assert len(solutions) == 4
    assert frozenset({'r1', 'r2'}) in solutions
    assert frozenset({'r1', 'r3'}) in solutions
    assert frozenset({'r4', 'r2'}) in solutions
    assert frozenset({'r4', 'r3'}) in solutions


# ---------------------------------------------------------------------------
# 6. Invalid bounds
# ---------------------------------------------------------------------------


def test_invalid_bounds_hi_less_than_lo():
    with pytest.raises(ValueError, match='Invalid bounds'):
        collect_solutions({'r1': ['A']}, bounds={'A': (3, 1)})


def test_invalid_bounds_negative_lo():
    with pytest.raises(ValueError, match='Invalid bounds'):
        collect_solutions({'r1': ['A']}, bounds={'A': (-1, 2)})


# ---------------------------------------------------------------------------
# 7. Edge cases
# ---------------------------------------------------------------------------


def test_bounds_zero_zero_blocks_rows():
    """A with (0,0) means no row covering A can be selected."""
    constraints = {
        'r1': ['A', 'B'],
        'r2': ['B'],
    }
    solutions = collect_solutions(constraints, bounds={'A': (0, 0)})
    assert solutions == [frozenset({'r2'})]


def test_all_optional_primary_items():
    """A(0,1) and B(0,1) with independent rows — all subsets should be valid."""
    constraints = {
        'r1': ['A'],
        'r2': ['B'],
    }
    solutions = collect_solutions(constraints, bounds={'A': (0, 1), 'B': (0, 1)})
    assert len(solutions) == 4
    assert frozenset() in solutions
    assert frozenset({'r1'}) in solutions
    assert frozenset({'r2'}) in solutions
    assert frozenset({'r1', 'r2'}) in solutions


# ---------------------------------------------------------------------------
# 8. Regression: null-move must not re-select already-tried rows
# ---------------------------------------------------------------------------


def test_null_move_no_duplicate_solutions():
    """Regression for duplicate solutions via null-move in tweaking mode.

    X has bounds (1,2) and Y has bounds (1,1).
    r1 covers X+Y; r2 covers X only.
    Valid solutions: {r1} (X covered once) and {r1,r2} (X covered twice).

    Before the fix, the null-move sub-search for X could re-select r1 for Y
    (r1 was still visible in Y's column after being tweaked out of X's column),
    producing a duplicate {r1}.  The collect_solutions helper asserts no
    duplicates, so this test would have failed with the old code.
    """
    constraints = {
        'r1': ['X', 'Y'],
        'r2': ['X'],
    }
    solutions = collect_solutions(constraints, bounds={'X': (1, 2)})
    assert len(solutions) == 2
    assert frozenset({'r1'}) in solutions
    assert frozenset({'r1', 'r2'}) in solutions


def test_null_move_lower_bound_respected():
    """Regression: null-move must not fire when lo has not yet been met.

    X has bounds (1,2), Y has bounds (1,1).
    r1 covers X+Y; r2 covers X only; r3 covers Y only.

    r3 covers Y without touching X.  If Y=r3 is chosen, X has had zero
    actual coverages when its level is entered (bound goes 2→1, slack=1).
    bound == slack at that point — previously the null-move condition
    `bound <= slack` fired, producing the invalid solution {r3} where X is
    covered 0 times (< lo=1).

    Valid solutions are {r1}, {r1,r2}, and {r2,r3} only (3 total).
    """
    constraints = {
        'r1': ['X', 'Y'],
        'r2': ['X'],
        'r3': ['Y'],
    }
    solutions = collect_solutions(constraints, bounds={'X': (1, 2)})
    assert len(solutions) == 3
    assert frozenset({'r1'}) in solutions
    assert frozenset({'r1', 'r2'}) in solutions
    assert frozenset({'r2', 'r3'}) in solutions


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
