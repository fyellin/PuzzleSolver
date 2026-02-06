import math
from typing import Optional, Literal
from galois import GF, Poly, berlekamp_massey, Field, FieldArray, ReedSolomon
import numpy as np


class MyReedSolomon:
    def __init__(self, n, k, field=None, alpha: Optional[int]=None, c: int = 1, systematic: bool = True):
        self.field = field or GF(2 ** 8)
        self.alpha = field(alpha) if alpha else self.field.primitive_element
        self.n = n
        self.k = k
        self.c = c
        self.d = n - k
        self.is_systemic = systematic
        self.distance = n - k
        self.roots = self.alpha ** (c + np.arange(0, self.distance))
        self.generator_poly = Poly.Roots(self.roots)
        self.x_to_the_distance = Poly.Degrees([self.distance], field=self.field)
        self.G = self.build_g()
        self.H = self.build_h()

    def encode(self, message, output: Literal['message', 'parity'] = 'message'):
        assert output in ('message', 'parity')
        if not self.is_systemic and output == 'parity':
            raise ValueError("output=parity makes no sense for non-systemic messages")
        length = len(message)
        assert 0 <= length <= self.k
        result = self.field(message) @ self.G[-len(message):]
        if output == 'parity':
            return result[-self.d:]
        else:
            return result[self.k - length:]

    def decode(self, message, output: Literal['message', 'codeword'] ='message', erasures=(), berlekamp_massey=False):
        assert output in ('message', 'codeword')
        length = len(message)
        assert self.distance <= length <= self.n
        if length == self.n:
            result = self._fix_message_errors(self.field(message), erasures, berlekamp_massey)
        else:
            pad_length = self.n - length  # number of zeroes elided from data
            # Create the actual full message with all zeros. Also update erasures to refer
            # to the indices in full_message rather than message
            full_message = self.field(np.pad(message, (pad_length, 0)), copy=False)
            erasures = [e + pad_length for e in erasures]
            result = self._fix_message_errors(full_message, erasures, berlekamp_massey)
            assert all(result[i] == 0 for i in range(pad_length)), "Data in elided area"

        quotient, remainder = divmod(Poly(result), self.generator_poly)
        if remainder.degree != 0:
            raise ValueError("Expected result to be a multiple of generator polynomial")

        # Systemic or not??   Padded or not??  'codework' or 'message?
        if output == 'message':
            result = result[:self.k] if self.is_systemic else quotient.coefficients(self.k)
        if length != self.n:
            assert max(result[0:pad_length]) == 0, "Result must start with zeros"
            result = result[pad_length:]
        return result

    def _fix_message_errors(self, in_message: FieldArray, erasures: list[int], bm: bool):
        assert len(in_message) == self.n
        message = Poly(in_message, field=self.field)
        syndrome = Poly(message(self.roots), order='asc')
        syndrome2 = Poly(self.H @ in_message, order='asc')
        assert syndrome == syndrome2, (syndrome, syndrome2)
        if syndrome.degree == 0:
            return self.field(in_message)

        if erasures:
            # Convert erasures from array indices to polynomial powers in the syndrome.
            erasures = [self.n - i - 1 for i in erasures]
            # The negative is needed for fields where characteristic prime ≠ 2.
            erasure_locator = math.prod(Poly([- self.alpha ** i, 1], field=self.field)
                                            for i in erasures)
            error_syndrome = (syndrome * erasure_locator) % self.x_to_the_distance
        else:
            erasure_locator = Poly.One(self.field)
            error_syndrome = syndrome

        if bm:
            locator = berlekamp_massey(error_syndrome.coefficients(order='asc')).reverse()
        else:
            locator, omega = self.sugiyama_get_locators(error_syndrome, len(erasures))

        if erasures:
            locator *= erasure_locator
        if erasures or bm:
            omega = (locator * syndrome) % self.x_to_the_distance

        locator_roots = locator.roots()
        error_positions = (locator_roots ** -1).log()
        if any(log > self.n for log in error_positions):
            raise ValueError(f"Bad error positions {error_positions}")

        # Calculate the Forney error. Note that we calculate the negative of the magnitude (avoiding
        # a negation), and then add it to our codeword rather than subtract it.
        error_magnitudes = omega(locator_roots) / locator.derivative()(locator_roots)
        if self.c != 1:
            error_magnitudes *= locator_roots ** (self.c - 1)
        fixed_message = message + Poly.Degrees(error_positions, error_magnitudes)
        return fixed_message.coefficients(self.n)

    def sugiyama_get_locators(self, syndromes: Poly, erasure_count:int = 0) -> tuple[Poly, Poly]:
        old_r, new_r = self.x_to_the_distance, syndromes
        old_s, new_s = Poly.Zero(self.field), Poly.One(self.field)
        while new_r.degree >= (self.distance + erasure_count) / 2:
            old_r, (q, new_r) = new_r, divmod(old_r, new_r)
            old_s, new_s = new_s, (old_s - q * new_s)
        return new_s, new_r

    def build_g(self):
        n, k, generator_poly = self.n, self.k, self.generator_poly
        assert generator_poly.degree == n - k
        assert generator_poly.coeffs[0] == 1
        generator_coeffs = generator_poly.coeffs[1:]
        result = self.field(np.eye(k, M=n, dtype=self.field.dtypes[0]), copy=False)
        if self.is_systemic:
            right = result[:, k:]  #  right side of the matrix.
            right[k - 1] = generator_coeffs
            for row in reversed(range(k - 1)):
                right[row, :-1] = right[row + 1, 1:]
                right[row] -= right[row + 1, 0] * generator_coeffs
        else:
            for row in range(0, k):
                result[row, row + 1:row + n - k + 1] = generator_coeffs
        return result

    def build_h(self):
        return  np.power.outer(self.roots, np.arange(self.n - 1, -1, -1))


def test1():
    for gf in (2**4, 2**8, 257, 3**6):
        field = GF(gf)
        print(field)
        for c in (0, 1, 2):
            rs = MyReedSolomon(15, 5, field, c=c)
            for start_message in ([1, 2, 3, 4, 5], [6, 7, 8]):
                message = rs.encode(start_message)
                bad_message = message.copy()
                bad_message[0:3] = [0, 0, 0]
                bad_message[-2] = 0
                for bm in (True,):
                    assert np.array_equal(message, result := rs.decode(bad_message,
                                                                       output='codeword',
                                                                       berlekamp_massey=bm)), result
                    assert np.array_equal(message, result := rs.decode(message,
                                                                       output='codeword',
                                                                       berlekamp_massey=bm)), result
                    assert np.array_equal(start_message, result := rs.decode(bad_message,
                                                                             output='message',
                                                                             berlekamp_massey=bm)), result
                    assert np.array_equal(start_message, result := rs.decode(message,
                                                                             output='message',
                                                                             berlekamp_massey=bm)), result

    return 'Finished'

def test2():
    for gf in (2**4, 2**8, 257, 3**6):
        field = GF(gf)
        print(field)
        for c in (0, 1, 2):
            rs = MyReedSolomon(15, 5, field, c=c)
            for start_message in ([1, 2, 3, 4, 5], [6, 7, 8]):
                message = rs.encode(start_message)
                bad_message = message.copy()
                bad_message[0:2] = bad_message[10:12] = (0, 0)
                erasures = (0, 1, 10)
                for bm in (True, False):
                    try:
                        result = rs.decode(bad_message, output='codeword',
                                           erasures=erasures, berlekamp_massey=bm)
                        if not np.array_equal(message, result):
                            temp = [f"{expected}/{actual}" if expected != actual else f"{expected}"
                                    for expected, actual in zip(message, result)]
                            print(f"{field.order} {c} {len(message)} {bm} [{' '.join(temp)}]")
                    except Exception as e:
                            print(f"{field.order} {c} {len(message)} {bm} {e}")


def test3():
    for gf in (31, 2**8, 11**2):
        field = GF(gf)
        print(field)
        for systematic in (False, ):
            rs1 = ReedSolomon(15, 5, field=field, systematic=systematic)
            rs2 = MyReedSolomon(15, 5, field=field, c=rs1.c, alpha=rs1.alpha, systematic=systematic)
            message = field([2, 3, 5, 7, 11])
            if not list(result1 := rs1.encode(message)) == (result2 := list(rs2.encode(message))):
                print('Encoding not the same')
                print(f'{result1=!r}')
                print(f'{result2=!r}')
            message2 = field([0, 0, 0, 6, 8])
            t1 = rs2.encode(message2)
            t2 = rs2.encode(message2[3:])
            assert t1[0] == t1[1] == t1[2] == 0
            assert np.array_equal(t1[3:], t2)
            t3 = rs1.encode(message2[3:])
            assert np.array_equal(t2, t3)
            fix1 = rs1.decode(t2)
            fix2 = rs2.decode(t2)
            assert np.array_equal(fix1, fix2)
            assert np.array_equal(fix1, message2[3:])


if __name__ == '__main__':
    # test1()
    # test2()
    test3()
