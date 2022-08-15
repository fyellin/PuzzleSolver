from __future__ import division

import functools
from fractions import Fraction

try:
    from fractions import gcd
except:
    from math import gcd


Problem7.pyΩ

if __name__ == '__main__':
    result = solution('4', '7')
    print(result, result == '4')

    result = solution('2', '1')
    print(result, result=='1')
