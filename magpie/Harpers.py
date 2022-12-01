from collections import Counter

from solver import DancingLinks
from solver import Encoder


LOOPS = [
    (1, 2, 3, 4, 5),
    (1, 6, 7, 8, 9),
    (2, 10, 11, 12, 6),
    (3, 13, 14, 30, 10),
    (4, 13, 15, 16, 17),
    (9, 5, 17, 18, 19),
    (8, 19, 20, 29, 28),
    (7, 12, 25, 27, 28),
    (25, 26, 23, 30, 11),
    (15, 14, 23, 24, 22),
    (22, 16, 18, 20, 21),
    (21, 24, 26, 27, 29)
]

WORDS = ["TREES", "AGREE", "NAOMI", "ROLES", "ASTER", "APNEA", "APTER", "ATTAR",]

def run():
    seen = {}
    for loop in LOOPS:
        for digit in loop:
            if digit not in seen:
                seen[digit] = loop

    encoder = Encoder.of_alphabet()
    constraints = {}
    optional_constraints = set()
    for word in WORDS:
        for loop in LOOPS:
            for start in range(5):
                xloop = loop[start:] + loop[:start]
                if 30 in xloop and word[xloop.index(30)] != 'I':
                    continue
                constraint = [x for letter, digit in zip(word, xloop)
                              if letter != '.'
                              for x in encoder.encode(letter, (digit, 0), seen[digit] == loop)]
                optional_constraints.update(constraint)
                constraint.append(word)
                name = word + "-".join(str(digit) for digit in xloop)
                constraints[name] = constraint
    links = DancingLinks(constraints, optional_constraints=optional_constraints)
    links.solve()



if __name__ == '__main__':
    run()
