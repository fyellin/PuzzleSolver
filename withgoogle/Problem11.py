from __future__ import division
from fractions import Fraction

from itertools import tee

def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def solution(pegs):
    if len(pegs) <= 1:
        return [-1, -1]
    delta = [b - a for a, b in pairwise(pegs)]
    sizes = [0]
    for d in delta:
        sizes.append(d - sizes[-1])
    if len(sizes) & 1:
        result = Fraction(-2) * sizes[-1]
    else:
        result = Fraction(2, 3) * sizes[-1]
    for i, value in enumerate(sizes):
        if i & 1 == 0:
            sizes[i] = value + result
        else:
            sizes[i] = value - result
    assert sizes[0] == 2 * sizes[-1]
    if min(sizes) >= 1:
        return [result.numerator, result.denominator]
    else:
        return [-1, -1]



if __name__ == '__main__':
    print(solution([4, 30, 50]))
    print(solution([4, 17, 50]))
    print(solution([1, 8, 20, 40]))
