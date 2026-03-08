"""Tests for DancingLinks and DancingLinksBounds (Algorithm X / Algorithm M)."""

from __future__ import annotations

import pytest

from solver.dancing_links import DancingLinks, DancingLinksBounds, DLConstraint


@pytest.fixture(params=[DancingLinks, DancingLinksBounds])
def solver_class(request):
    return request.param


def collect_solutions(
    solver_class,
    constraints: dict[str, list[DLConstraint]],
    *,
    optional_constraints: set[str] | None = None,
) -> list[frozenset[str]]:
    """Run the solver and return a sorted list of solutions."""
    solutions: list[frozenset[str]] = []
    dl = solver_class(
        constraints,
        row_printer=lambda rows: solutions.append(frozenset(rows)),
        optional_constraints=optional_constraints or set(),
    )
    dl.solve()
    return sorted(solutions)


def test_knuth_classic_example(solver_class):
    """Knuth's original Algorithm X example from the Dancing Links paper."""
    constraints: dict[str, list[str]] = {
        "A": ["3", "5", "6"],
        "B": ["1", "4", "7"],
        "C": ["2", "3", "6"],
        "D": ["1", "4"],
        "E": ["2", "7"],
        "F": ["4", "5", "7"],
    }
    solutions = collect_solutions(solver_class, constraints)
    assert solutions == [frozenset({"A", "D", "E"})]


def test_no_solution(solver_class):
    """Problem with no solution (required column left uncoverable)."""
    constraints: dict[str, list[str]] = {
        "r1": ["A", "B"],
        "r2": ["A", "C"],
    }
    solutions = collect_solutions(solver_class, constraints)
    assert solutions == []


def test_empty_constraints_is_trivial_solution(solver_class):
    """No items mean the empty set is the only solution."""
    solutions = collect_solutions(solver_class, constraints={})
    assert solutions == [frozenset()]


def test_secondary_optional_constraint_at_most_once(solver_class):
    """Secondary (optional) uncolored constraints are enforced at-most-once.

    A and B are primary (must be covered exactly once). Secondary constraint S may
    be used but cannot appear in more than one chosen row.
    """
    constraints: dict[str, list[DLConstraint]] = {
        "r1": ["A", "S"],
        "r2": ["B", "S"],
        "r3": ["A"],
        "r4": ["B"],
    }
    solutions = collect_solutions(solver_class, constraints, optional_constraints={"S"})
    assert len(solutions) == 3
    assert frozenset({"r3", "r4"}) in solutions
    assert frozenset({"r1", "r4"}) in solutions
    assert frozenset({"r3", "r2"}) in solutions


def test_colors_basic(solver_class):
    """Secondary colored constraint enforces consistent color across the solution.

    P can only be covered once; solutions are single rows {r1}, {r2}, {r3}.
    """
    constraints: dict[str, list[DLConstraint]] = {
        "r1": ["P", ("S", "red")],
        "r2": ["P", ("S", "blue")],
        "r3": ["P"],
    }
    solutions = collect_solutions(solver_class, constraints, optional_constraints={"S"})
    assert len(solutions) == 3
    assert frozenset({"r1"}) in solutions
    assert frozenset({"r2"}) in solutions
    assert frozenset({"r3"}) in solutions


def test_colors_conflict_eliminates_rows(solver_class):
    """Inconsistent colors for the same secondary colored constraint are rejected."""
    constraints: dict[str, list[DLConstraint]] = {
        "r1": ["P1", ("S", "red")],
        "r2": ["P1", ("S", "blue")],
        "r3": ["P2", ("S", "red")],
        "r4": ["P2", ("S", "blue")],
    }
    solutions = collect_solutions(solver_class, constraints, optional_constraints={"S"})
    assert len(solutions) == 2
    assert frozenset({"r1", "r3"}) in solutions
    assert frozenset({"r2", "r4"}) in solutions


def test_colors_with_optional_colored_constraint(solver_class):
    """A colored secondary constraint can be used (even though it's optional)."""
    constraints: dict[str, list[DLConstraint]] = {
        "r1": ["P1", ("S", "red")],
        "r2": ["P2", ("S", "red")],
        "r3": ["P1", ("S", "blue")],
        "r4": ["P2"],  # doesn't mention S
    }

    # Primary items P1 & P2 must both be covered.
    # If we pick r1, then P2 must be satisfied by r2 (to keep S=red consistent),
    # or by r4 (S unused on that row).
    # If we pick r3 (P1 + S:blue), P2 can be r4: P2 without S is valid—optional
    # secondaries do not force every row to mention S or match a color.
    solutions = collect_solutions(solver_class, constraints, optional_constraints={"S"})
    assert set(solutions) == {
        frozenset({"r1", "r2"}),
        frozenset({"r1", "r4"}),
        frozenset({"r3", "r4"}),
    }


def test_colored_constraint_must_be_optional(solver_class):
    constraints: dict[str, list[DLConstraint]] = {"r1": [("S", "red")]}  # S not optional
    dl = solver_class(constraints)
    with pytest.raises(ValueError, match="optional"):
        dl.create_data_structure()


def test_multiple_solutions(solver_class):
    """3-item problem with 4 solutions."""
    constraints = {
        'r_AB': ['A', 'B'],
        'r_AC': ['A', 'C'],
        'r_BC': ['B', 'C'],
        'r_A': ['A'],
        'r_B': ['B'],
        'r_C': ['C'],
    }
    solutions = collect_solutions(solver_class, constraints)
    assert len(solutions) == 4
    assert frozenset({'r_AB', 'r_C'}) in solutions
    assert frozenset({'r_AC', 'r_B'}) in solutions
    assert frozenset({'r_BC', 'r_A'}) in solutions
    assert frozenset({'r_A', 'r_B', 'r_C'}) in solutions


def test_single_item_single_row(solver_class):
    constraints = {'r1': ['A']}
    solutions = collect_solutions(solver_class, constraints)
    assert solutions == [frozenset({'r1'})]


def test_multiple_secondary_colors(solver_class):
    """Two secondary items S1 and S2 — only color-consistent pairs survive."""
    constraints = {
        'r1': ['P1', ('S1', 'red'), ('S2', 'x')],
        'r2': ['P1', ('S1', 'blue'), ('S2', 'y')],
        'r3': ['P2', ('S1', 'red'), ('S2', 'x')],
        'r4': ['P2', ('S1', 'blue'), ('S2', 'y')],
    }
    solutions = collect_solutions(solver_class, constraints, optional_constraints={'S1', 'S2'})
    assert len(solutions) == 2
    assert frozenset({'r1', 'r3'}) in solutions
    assert frozenset({'r2', 'r4'}) in solutions


def test_duplicate_constraints_in_row_raises(solver_class):
    constraints: dict[str, list[str]] = {"r1": ["A", "A"]}
    dl = solver_class(constraints)
    with pytest.raises(ValueError, match="duplicate"):
        dl.create_data_structure()


# ---------------------------------------------------------------------------
# show() tests
# ---------------------------------------------------------------------------


def _build(solver_class, constraints, *, optional_constraints=None):
    """Create a solver and populate its data structure without running the search."""
    dl = solver_class(constraints, optional_constraints=optional_constraints or set(), color=False)
    dl.data = dl.create_data_structure()
    return dl


def test_show_root_and_second_root(solver_class):
    """show() identifies the two sentinel header nodes by name."""
    dl = _build(solver_class, {"r1": ["A"]})
    assert dl.show(0) == "ROOT"
    assert dl.show(len(dl.data.left) - 1) == "SECOND_ROOT"


def test_show_primary_headers(solver_class):
    """show() returns the sorted constraint name for each primary header node.

    constraints {"r1": ["A","B"], "r2": ["B","C"]} produce three primary headers:
    index 1 = A, index 2 = B, index 3 = C (sorted alphabetically).
    """
    dl = _build(solver_class, {"r1": ["A", "B"], "r2": ["B", "C"]})
    assert dl.show(1) == "A"
    assert dl.show(2) == "B"
    assert dl.show(3) == "C"


def test_show_secondary_header(solver_class):
    """show() returns the constraint name for a secondary (optional) header node.

    With primary P and secondary S: header layout is 0=ROOT, 1=P, 2=S, 3=SECOND_ROOT.
    """
    dl = _build(
        solver_class,
        {"r1": ["P", ("S", "red")], "r2": ["P", ("S", "blue")]},
        optional_constraints={"S"},
    )
    assert dl.show(2) == "S"


def test_show_spacer_node(solver_class):
    """show() returns "<row_name>" for a row spacer node.

    Header nodes occupy indices 0..4 (3 primary + ROOT + SECOND_ROOT), so the
    first spacer is at index 5 and the second at index 8.
    """
    dl = _build(solver_class, {"r1": ["A", "B"], "r2": ["B", "C"]})
    assert dl.show(5) == "<r1>"
    assert dl.show(8) == "<r2>"


def test_show_spacer_verbose_no_color(solver_class):
    """show() with verbose=True appends the row's constraint names."""
    dl = _build(solver_class, {"r1": ["A", "B"], "r2": ["B", "C"]})
    assert dl.show(5, verbose=True) == "<r1>: A, B"
    assert dl.show(8, verbose=True) == "<r2>: B, C"


def test_show_data_node_no_color(solver_class):
    """show() returns "<row constraint>" for a plain (uncolored) data node.

    Layout after three primary headers (0..4):
      5=spacer r1, 6=r1-A, 7=r1-B, 8=spacer r2, 9=r2-B, 10=r2-C
    """
    dl = _build(solver_class, {"r1": ["A", "B"], "r2": ["B", "C"]})
    assert dl.show(6) == "<r1 A>"
    assert dl.show(7) == "<r1 B>"
    assert dl.show(9) == "<r2 B>"
    assert dl.show(10) == "<r2 C>"


def test_show_data_node_with_color(solver_class):
    """show() appends "/color" for secondary nodes that carry a color.

    Layout with primary P and secondary S (header indices 0..3):
      4=spacer r1, 5=r1-P, 6=r1-S/red, 7=spacer r2, 8=r2-P, 9=r2-S/blue
    """
    dl = _build(
        solver_class,
        {"r1": ["P", ("S", "red")], "r2": ["P", ("S", "blue")]},
        optional_constraints={"S"},
    )
    assert dl.show(5) == "<r1 P>"
    assert dl.show(6) == "<r1 S/red>"
    assert dl.show(8) == "<r2 P>"
    assert dl.show(9) == "<r2 S/blue>"


def test_show_spacer_verbose_with_color(solver_class):
    """show() verbose on a spacer lists all items with no marking."""
    dl = _build(
        solver_class,
        {"r1": ["P", ("S", "red")], "r2": ["P", ("S", "blue")]},
        optional_constraints={"S"},
    )
    assert dl.show(4, verbose=True) == "<r1>: P, S/red"
    assert dl.show(7, verbose=True) == "<r2>: P, S/blue"


def test_show_data_node_verbose_no_color(solver_class):
    """show() verbose on a data node lists all items and brackets the one at index.

    Layout: 5=spacer r1, 6=r1-A, 7=r1-B, 8=spacer r2, 9=r2-B, 10=r2-C
    """
    dl = _build(solver_class, {"r1": ["A", "B"], "r2": ["B", "C"]})
    assert dl.show(6, verbose=True) == "<r1>: [A], B"
    assert dl.show(7, verbose=True) == "<r1>: A, [B]"
    assert dl.show(9, verbose=True) == "<r2>: [B], C"
    assert dl.show(10, verbose=True) == "<r2>: B, [C]"


def test_show_data_node_verbose_with_color(solver_class):
    """show() verbose on a colored secondary node brackets that item.

    Layout: 4=spacer r1, 5=r1-P, 6=r1-S/red, 7=spacer r2, 8=r2-P, 9=r2-S/blue
    """
    dl = _build(
        solver_class,
        {"r1": ["P", ("S", "red")], "r2": ["P", ("S", "blue")]},
        optional_constraints={"S"},
    )
    assert dl.show(5, verbose=True) == "<r1>: [P], S/red"
    assert dl.show(6, verbose=True) == "<r1>: P, [S/red]"
    assert dl.show(8, verbose=True) == "<r2>: [P], S/blue"
    assert dl.show(9, verbose=True) == "<r2>: P, [S/blue]"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
