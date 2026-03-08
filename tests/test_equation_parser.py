# ruff: noqa: E302
import pytest

from solver.equation_parser import EquationParser, Parse

_parser = EquationParser()


def _parse1(text: str) -> Parse:
    """Parse a single-expression string and return the one Parse."""
    result = _parser.parse(text)
    assert len(result) == 1
    return result[0]


# --- atoms ---

def test_number():
    assert _parse1('42').expression == 42

def test_variable():
    assert _parse1('x').expression == 'x'

def test_long_name():
    assert _parse1('$xy').expression == 'xy'


# --- binary operators ---

def test_addition():
    assert _parse1('a + b').expression == ('+', 'a', 'b')

def test_subtraction():
    assert _parse1('a - b').expression == ('-', 'a', 'b')

def test_multiplication():
    assert _parse1('a * b').expression == ('*', 'a', 'b')

def test_division():
    assert _parse1('a / b').expression == ('/', 'a', 'b')

def test_power_caret():
    assert _parse1('a ^ b').expression == ('**', 'a', 'b')

def test_power_stars():
    assert _parse1('a ** b').expression == ('**', 'a', 'b')

def test_unicode_minus():
    assert _parse1('a − b').expression == ('-', 'a', 'b')

def test_unicode_times():
    assert _parse1('a × b').expression == ('*', 'a', 'b')


# --- precedence and associativity ---

def test_left_associative():
    assert _parse1('a + b - c').expression == ('-', ('+', 'a', 'b'), 'c')

def test_mul_over_add():
    assert _parse1('a + b * c').expression == ('+', 'a', ('*', 'b', 'c'))

def test_mul_over_add_left():
    assert _parse1('a * b + c').expression == ('+', ('*', 'a', 'b'), 'c')

def test_parentheses():
    assert _parse1('(a + b) * c').expression == ('*', ('+', 'a', 'b'), 'c')

def test_juxtaposition_over_add():
    assert _parse1('AB + C').expression == ('+', ('*', 'A', 'B'), 'C')

def test_juxtaposition_over_add_right():
    assert _parse1('A + BC').expression == ('+', 'A', ('*', 'B', 'C'))

def test_unary_over_mul():
    # unary minus binds tighter than multiply: -a * b = (-a) * b
    assert _parse1('-a * b').expression == ('*', ('-', 'a'), 'b')

def test_power_over_mul():
    assert _parse1('a ** b * c').expression == ('*', ('**', 'a', 'b'), 'c')

def test_power_right_associative():
    # a ** b ** c = a ** (b ** c)
    assert _parse1('a ** b ** c').expression == ('**', 'a', ('**', 'b', 'c'))

def test_power_over_unary():
    # power binds tighter than prefix unary: -a**b = -(a**b)
    assert _parse1('-a ** b').expression == ('-', ('**', 'a', 'b'))

def test_postfix_over_power():
    # postfix binds tighter than power: a! ** b = (a!) ** b
    assert _parse1('a! ** b').expression == ('**', ('!', 'a'), 'b')

def test_postfix_over_prefix():
    temp = _parse1('-√a\'!').expression
    assert temp == ('-', ('√', ('!', ('\'', 'a'))))

def test_all_precedence_interactions():
    # -√a!b'^cd = -(√(a!) * (b')^c * d)
    parse = _parse1("-√a!b'^cd")
    assert parse.expression == (
        '-', ('*', ('*', ('√', ('!', 'a')), ('**', ("'", 'b'), 'c')), 'd'))
    assert parse.to_string() == "-((sqrt(fact(a)) * (prime(b) ** c)) * d)"
    assert parse.to_string(concise=True) == "-(sqrt(fact(a)) * prime(b) ** c * d)"

def test_all_precedence_interactions2():
    parse = _parse1(" -√a! ** b' * +c + d / e - f ")
    assert parse.expression == (
        '-', ('+', ('*', ('-', ('√', ('**', ('!', 'a'), ("'", 'b')))), ('+', 'c')),
               ('/', 'd', 'e')), 'f')
    assert parse.to_string() == '(((-sqrt(fact(a) ** prime(b))) * (+c)) + (d / e)) - f'
    assert parse.to_string(concise=True) == '-sqrt(fact(a) ** prime(b)) * +c + d / e - f'
    assert parse.to_string(concise=True, pure=True) == '-√a! ** b\' * +c + d / e - f'

def test_precedence_bug():
    # Verify that a bug has been fixed.
    parse = _parse1("(a + b)!")
    assert parse.to_string(pure=True, concise=True) == '(a + b)!'

# --- juxtaposition ---

def test_juxtaposition_two():
    assert _parse1('AB').expression == ('*', 'A', 'B')

def test_juxtaposition_three():
    assert _parse1('ABC').expression == ('*', ('*', 'A', 'B'), 'C')


# --- unary prefix ---

def test_unary_minus():
    assert _parse1('-a').expression == ('-', 'a')

def test_unary_plus():
    assert _parse1('+a').expression == ('+', 'a')

def test_sqrt():
    assert _parse1('√a').expression == ('√', 'a')

def test_unary_chain():
    assert _parse1('-+√a').expression == ('-', ('+', ('√', 'a')))


# --- postfix ---

def test_factorial():
    assert _parse1('a!').expression == ('!', 'a')

def test_prime():
    assert _parse1("a'").expression == ("'", 'a')

def test_postfix_chain():
    assert _parse1("a!'").expression == ("'", ('!', 'a'))


# --- functions and getitem ---

def test_function_new_syntax():
    assert _parse1('@f(a, b)').expression == ('function', 'f', ('a', 'b'))

def test_function_old_syntax():
    assert _parse1('"sin"(x)').expression == ('function', 'sin', ('x',))

def test_function_no_args():
    assert _parse1('@f()').expression == ('function', 'f', ())

def test_getitem():
    assert _parse1('@h[a, b]').expression == ('getitem', 'h', ('a', 'b'))

def test_getitem_empty():
    assert _parse1('@h[]').expression == ('getitem', 'h', ())


# --- multiple equations ---

def test_multiple_equations():
    result = _parser.parse('a = b = c')
    assert len(result) == 3
    assert [p.expression for p in result] == ['a', 'b', 'c']


# --- vars() ---

def test_vars_basic():
    assert _parse1('a + b * c').vars() == ['a', 'b', 'c']

def test_vars_deduplicates():
    assert _parse1('a + a').vars() == ['a']

def test_vars_const_only():
    assert _parse1('42').vars() == []

def test_vars_inside_function():
    assert _parse1('@f(a, b)').vars() == ['a', 'b']

def test_vars_long_name():
    assert _parse1('$xy + a').vars() == ['a', 'xy']


# --- str() / to_string() ---

def test_str_simple():
    assert str(_parse1('a + b')) == 'a + b'

def test_str_preserves_precedence():
    assert str(_parse1('a + b * c')) == 'a + b * c'

def test_str_factorial():
    assert str(_parse1('a!')) == 'fact(a)'

def test_str_sqrt():
    assert str(_parse1('√a')) == 'sqrt(a)'

def test_str_to_string_with_parens():
    assert _parse1('(a + b) * c').to_string() == '(a + b) * c'


# --- error handling ---

def test_syntax_error():
    with pytest.raises(SyntaxError):
        _parser.parse('a +')
