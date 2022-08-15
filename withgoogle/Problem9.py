from __future__ import division

import functools
from fractions import Fraction


def solution(items):
    return sorted(items, key=lexical)

def lexical(token):
    return tuple(int(part) for part in token.split('.'))

if __name__ == '__main__':
    result = solution(["1.11", "2.0.0", "1.2", "2", "0.1", "1.2.1", "1.1.1", "2.0"])
    print(result)
    result = solution(["1.1.2", "1.0", "1.3.3", "1.0.12", "1.0.2"])
    print(result)
