from functools import cache
from itertools import combinations

PRIMES = [11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]

@cache
def rev(x):
    return int(str(x)[::-1])


def foobar():
    for k, C in combinations(PRIMES, 2):
        a = k * k - 2 * k + 2
        if not (100 <= a < 1000): continue
        K = a - 2 * C
        if not (k < K < C): continue
        for p in range(K + 1, C):
            O = p - K
            T = p - C + k + rev(K)
            if not (k < O < T < K):
                continue
            if p != rev(T) + rev(k):
                continue
            A = (k - 2) * O
            if not (a < A < 1000): continue
            for S in range(a + 1, A):
                r = C - p - rev(p) - S + T * k
                t = r + T
                if S != p - O + r + K:
                    continue
                if not (a < r < t < S < A):
                    continue
                R = p * (O + K) + T
                e = (R + S) * (rev(p) - K) - rev(T) - k
                n = S * (rev(C) - rev(p)) - rev(S) + rev(K) + e
                print(f'{k=}; {O=}; {T=}; {K=}; {p=}; {C=}; {a=}; {r=}; {t=}; {S=}; {A=}; {R=}; {e=}; {n=}')


if __name__ == '__main__':
    result = foobar()
    print(result)

"""
k=17; p=96; a=257; r=345; t=397; e=58392; n=62964
O=33; T=52; K=63; C=97; S=471; A=495; N=xxxx, R=9268; 

k=17; p=96; r=345;                                                                                          
O=33; T=52;   N=xxxx, 


"""
