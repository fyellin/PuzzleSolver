import functools
import math
from collections import defaultdict
from itertools import count, product
import re


def make_dice():
    result = defaultdict(list)
    for a in (1, 6):
        for b in (2, 5):
            for c in (3, 4):
                if ((a == 6) + (b == 5) + (c == 4)) % 2 == 0:
                    aa, bb, cc = a, b, c
                else:
                    aa, bb, cc = a, c, b
                result[aa].append((bb, cc))
                result[bb].append((cc, aa))
                result[cc].append((aa, bb))
    return result

"""
if x shows on the top of a die, then DICE[x] is the set of tuples (y, z) of all the
possibilities of y being the front and z being the right. Likewise, if x is on the front,
then (y, z) represent the right and top, since everything is circular.
"""
DICE = make_dice()


def is_square(x):
    return math.isqrt(x) ** 2 == x


def make_number(a, b, c, d):
    """Converts a list of four digits into a number"""
    return 1000 * a + 100 * b + 10 * c + d


def make_list(number):
    """Converts a number into a list of digits"""
    return tuple(int(x) for x in str(number))


def find_squares():
    """Find three four-digit squares that can be the top, front, and right side of four dice"""
    result = []
    for x in range(32, 100):
        t1, t2, t3, t4 = make_list(tt := (x * x))
        for (f1, r1), (f2, r2), (f3, r3), (f4, r4) in product(DICE[t1], DICE[t2], DICE[t3], DICE[t4]):
            if is_square(ff := make_number(f1, f2, f3, f4)) and is_square(rr := make_number(r1, r2, r3, r4)):
                result.append((tt, ff, rr))
    return result


def find_powers():
    """Find all results for "a number raised to a power greater than 2"""
    result = set()
    for power in count(3):
        if 2 ** power > 9999: break
        for base in count(2):
            value = base ** power
            if value < 1000: continue
            if value > 9999: break
            if re.fullmatch(r'[1-6]{4}', str(value)):
                result.add(value)
    return sorted(result)


def run_me():
    for t41, t42, t43, t44 in (make_list(t * t) for t in range(32, 100) if re.fullmatch('[1-6]{4}', str(t * t))):
        for (f41, r41), (f42, r42), (f43, r43), (f44, r44) in product(DICE[t41], DICE[t42], DICE[t43], DICE[t44]):
            if not is_square(make_number(f41, f42, f43, f44)): continue
            if not is_square(make_number(t41, t42, t43, t44)): continue
            for t1d, f4d in product(find_powers(), repeat=2):
                t11, t21, t31, t41x = make_list(t1d)
                f14, f24, f34, f44x = make_list(f4d)
                if t41 != t41x: continue
                if f44 != f44x: continue
                for (r14, t14), (r24, t24), (r34, t34) in product(DICE[f14], DICE[f24], DICE[f34]):
                    assert r44, t44 in DICE[f44]
                    for t12, t13 in product(range(1, 7), repeat=2):
                        t1a = make_number(t11, t12, t13, t14)
                        for y in range(1, 7):
                            if not is_square(t1a + y * y): continue
                            for t22, t23, t32, t33 in product(range(1, 7), repeat=4):
                                for x in range(1, 7):
                                    if x == y: continue
                                    if make_number(t12, t22, t32, t42) % (x * y) != 0: continue
                                    if make_number(t13, t23, t33, t43) % (x * y) != 0: continue
                                    top = (t11, t12, t13, t14, t21, t22, t23, t24, t31, t32, t33, t34, t41, t42, t43, t44)
                                    if top.count(x) != x: continue
                                    for w in range(1, 7):
                                        if w == x or w == y: continue
                                        if top.count(w) != w: continue
                                        for (f11, r11), (f21, r21), (f31, r31) in product(DICE[t11], DICE[t21], DICE[t31]):
                                            temp = make_number(f11, f21, f31, f41)
                                            for z in range(1, 7):
                                                if z in (w, x, y): continue
                                                if not is_square(temp - w * y * z): continue
                                                for (f12, r12), (f22, r22), (f32, r32) in product(DICE[t12], DICE[t22], DICE[t32]):
                                                    temp = make_number(r12, r22, r32, r42)
                                                    if temp % (x + z) != 0: continue
                                                    for (f13, r13), (f23, r23), (f33, r33) in product(DICE[t13], DICE[t23], DICE[t33]):
                                                        front = (f11, f12, f13, f14, f21, f22, f23, f24, f31, f32, f33, f34, f41, f42, f43, f44)
                                                        right = (r11, r12, r13, r14, r21, r22, r23, r24, r31, r32, r33, r34, r41, r42, r43, r44)
                                                        if front.count(y) != y: continue
                                                        if right.count(z) != z: continue
                                                        temp = make_number(r21, r22, r23, r24) + w
                                                        if (age := math.isqrt(temp)) ** 2 != temp: continue
                                                        temp = make_number(t31, t32, t33, t34)
                                                        if temp % age != 0: continue
                                                        temp = make_number(f13, f23, f33, f43)
                                                        if temp != sum(top + front + right) * x: continue
                                                        print(w, x, y, z, age, top, front, right)


def tryit():
    import re
    for square in [xx * xx for xx in range(31, 100)]:
        for w in range(1, 6):
            value  = square - w
            if re.fullmatch(r'[3641][4532][4532][2345]', str(value)):
                print(square, w, value)


def draw_me():
    from solver.draw_grid import draw_grid

    top = (6, 5, 4, 5, 5, 6, 4, 4, 6, 6, 6, 6, 1, 4, 4, 4)
    front = (4, 4, 1, 3, 6, 5, 1, 1, 4, 5, 2, 2, 4, 2, 2, 5)
    right = (5, 1, 5, 6, 4, 3, 5, 5, 5, 3, 4, 4, 2, 1, 1, 6)

    for x in (top, front, right):
        entries = dict(zip(product(range(1, 5), repeat=2), x))
        draw_grid(max_row=5, max_column=5,
                  clued_locations=set(product(range(1, 5), repeat=2)),
                  clue_values=entries,
                  location_to_clue_numbers={(1, 1): [1], (1, 2): [2], (1, 3): [3], (1, 4): [4], (2, 1): [5], (3, 1): [6], (4, 1): [7]},
                  location_to_entry=entries,
                  top_bars=set(),
                  left_bars=set())

@functools.cache
def possible_ages():
    import re
    return [age for age in range(32, 1000)
            if any(re.fullmatch(r'[1346][1-6][1-6][2345]', str(age * age - w)) for w in (1, 2, 3, 4, 5))]

TRIPLES = {
    (1, 2, 3), (1, 3, 5), (1, 5, 4), (1, 4, 2),
    (2, 1, 4), (2, 4, 6), (2, 6, 3), (2, 3, 1),
    (3, 1, 2), (3, 2, 6), (3, 6, 5), (3, 5, 1),
    (4, 1, 5), (4, 5, 6), (4, 6, 2), (4, 2, 1),
    (5, 1, 3), (5, 3, 6), (5, 6, 4), (5, 4, 1),
    (6, 2, 4), (6, 4, 5), (6, 5, 3), (6, 3, 2)}

def f1():
    import re
    squares = [f"{i * i - Y * Y} = {i * i} - {Y * Y}"
               for i in range(10, 100) for Y in (3, 4)
               if re.fullmatch('[16][1-6][2345][1256]', str(i * i - Y * Y))]
    print(squares)
    table = {(x, y): z for x, y, z in TRIPLES}
    for x in [x for x in squares if x % 10 == 5]:
        for y in [y for y in squares if y % 10 == 4]:
            pairs = list(zip(make_list(x), make_list(y)))
            result = [table.get(x) for x in pairs]
            if all(result):
                print(x, y, result, [7 - x for x in result])
