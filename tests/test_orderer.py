# ruff: noqa: E302
import pytest

from solver import Orderer


def _check_lt_le(orderer, count: int, is_lt: bool):
    for a in range(count):
        for b in range(count):
            disjoint = orderer.left(a).isdisjoint(orderer.right(b))
            expected = (a < b) if is_lt else (a <= b)
            assert disjoint == expected, f"a={a}, b={b}"
    all_used = (set().union(*(orderer.left(i) for i in range(count))) |
                set().union(*(orderer.right(i) for i in range(count))))
    assert orderer.all_codes() == all_used

def test_lt_int():
    _check_lt_le(Orderer.LT("x", 6), 6, is_lt=True)

def test_le_int():
    _check_lt_le(Orderer.LE("x", 6), 6, is_lt=False)

def test_lt_set():
    items = {'p', 'q', 'r', 's'}
    orderer = Orderer.LT("x", items)
    sorted_items = sorted(items)
    for a, va in enumerate(sorted_items):
        for b, vb in enumerate(sorted_items):
            disjoint = orderer.left(va).isdisjoint(orderer.right(vb))
            assert disjoint == (a < b), f"left({va}) disjoint right({vb})"

def test_le_set():
    items = {'p', 'q', 'r', 's'}
    orderer = Orderer.LE("x", items)
    sorted_items = sorted(items)
    for a, va in enumerate(sorted_items):
        for b, vb in enumerate(sorted_items):
            disjoint = orderer.left(va).isdisjoint(orderer.right(vb))
            assert disjoint == (a <= b), f"left({va}) disjoint right({vb})"

def test_lt_count_1():
    orderer = Orderer.LT("x", 1)
    assert not orderer.left(0).isdisjoint(orderer.right(0))

def test_le_count_1():
    orderer = Orderer.LE("x", 1)
    assert orderer.left(0).isdisjoint(orderer.right(0))

def test_eq_int():
    orderer = Orderer.EQ("e", 4)
    assert orderer.all_codes() == {orderer.code}
    for a in range(4):
        for b in range(4):
            (left_code, left_color) = next(iter(orderer.left(a)))
            (right_code, right_color) = next(iter(orderer.right(b)))
            assert left_code == right_code
            assert (left_color == right_color) == (a == b), f"a={a}, b={b}"

def test_eq_set():
    items = {'x', 'y', 'z'}
    orderer = Orderer.EQ("e", items)
    for va in sorted(items):
        for vb in sorted(items):
            left_color = next(iter(orderer.left(va)))[1]
            right_color = next(iter(orderer.right(vb)))[1]
            assert (left_color == right_color) == (va == vb)

def test_lt_out_of_bounds():
    orderer = Orderer.LT("x", 4)
    with pytest.raises(ValueError):
        orderer.left(-1)
    with pytest.raises(ValueError):
        orderer.left(4)
    with pytest.raises(ValueError):
        orderer.right(-1)
    with pytest.raises(ValueError):
        orderer.right(4)

def test_le_out_of_bounds():
    orderer = Orderer.LE("x", 4)
    with pytest.raises(ValueError):
        orderer.left(-1)
    with pytest.raises(ValueError):
        orderer.left(4)
    with pytest.raises(ValueError):
        orderer.right(-1)
    with pytest.raises(ValueError):
        orderer.right(4)

def test_eq_out_of_bounds():
    orderer = Orderer.EQ("e", 4)
    with pytest.raises(ValueError):
        orderer.left(-1)
    with pytest.raises(ValueError):
        orderer.left(4)

def test_lt_missing_key():
    orderer = Orderer.LT("x", {'a', 'b', 'c'})
    with pytest.raises(KeyError):
        orderer.left('z')
    with pytest.raises(KeyError):
        orderer.right('z')

def test_le_missing_key():
    orderer = Orderer.LE("x", {'a', 'b', 'c'})
    with pytest.raises(KeyError):
        orderer.left('z')
    with pytest.raises(KeyError):
        orderer.right('z')

def test_eq_missing_key():
    orderer = Orderer.EQ("e", {'a', 'b', 'c'})
    with pytest.raises(KeyError):
        orderer.left('z')
