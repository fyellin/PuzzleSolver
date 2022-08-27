from __future__ import division

import functools
from fractions import Fraction


def solution(n, base):
    cache = dict()
    length = len(n)
    current = tuple(int(ch) for ch in n)[::-1] # store with low bit at left
    cache[current] = len(cache)
    while True:
        temp1 = sorted(current)
        temp2 = temp1[::-1]
        result = [0] * length
        carry = 0
        for i, a, b in zip(range(length), temp1, temp2):
            result[i] = a - b + carry
            if result[i] < 0:
                result[i] += base
                carry = -1
            else:
                carry = 0
        assert carry == 0
        next = tuple(result)
        if next in cache:
            return len(cache) - cache[next]
        else:
            cache[next] = len(cache)
            current = next

if __name__ == '__main__':
    print(solution('1211', 10))
    print(solution('210022', 3))


