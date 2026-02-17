import math

from solver import ClueValue


def is_square(n):
    return 0 <= n == math.isqrt(n) ** 2


def is_cube(x):
    return round(x ** (1 / 3)) ** 3 == x


def is_triangular(n):
    if n < 0:
        return False
    discriminant = 8 * n + 1
    return is_square(discriminant)


def is_fibonacci(n):
    if n < 0:
        return False
    return is_square(5 * n * n + 4) or is_square(5 * n * n - 4)


def digit_product(x):
    return math.prod(int(i) for i in str(x))


def digit_sum(x):
    return sum(int(i) for i in str(x))


def extended_multiply_constraint(values, a, b, c) -> list[ClueValue]:
    if a is None:
        result = int(b) * int(c)
    else:
        result, r = divmod(int(a), int(b if c is None else c))
        if r != 0:
            return []
    result = str(result)
    return [result] if result in values else []


def extended_add_constraint(values, a, b, c) -> list[ClueValue]:
    if a is None:
        result = int(b) * int(c)
    else:
        result = int(a) - int(b if c is None else c)
        if result < 0:
            return []
    result = str(result)
    return [result] if result in values else []
