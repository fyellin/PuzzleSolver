import math


def is_square(n):
    return n >= 0 and math.isqrt(n) ** 2 == n

def is_triangular(n):
    if n < 0:
        return False
    # A number n is triangular if 8n + 1 is a perfect square
    discriminant = 8 * n + 1
    return is_square(discriminant)


def is_fibonacci(n):
    if n < 0:
        return False
    return is_square(5 * n * n + 4) or is_square(5 * n * n - 4)
