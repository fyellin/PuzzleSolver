import itertools
from collections import Counter

STRING = """
 TWENTTWO
VOHVISNOW
UXINGTXON
LITsREOWS
VWEVESTXW
IETESVEHI
FFIXEIOON
OTuENVFWG
REELEOFF """.lower().replace(' ', '').replace('\n','')

NUMBERS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
           "nine", "ten", "eleven", "twelve", "thirteen", "fourteen"]


def run(extra='', *, show=False):
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    letter_count = Counter(STRING)
    result = [extra]
    for letter in sorted(letter_count.keys()):
        result.append(letter)
        result.append(NUMBERS[letter_count[letter]])
    result_count = Counter(''.join(result))

    if show:
        letters = sorted(set(letter_count.keys()).union(set(result_count.keys())))
        for letter in letters:
            print(f'{letter.upper()} {letter_count[letter]:2} {result_count[letter]: 2}')

    if all(letter_count[letter] >= result_count[letter] for letter in alphabet):
        temp = [letter * (letter_count[letter] - result_count[letter]) for letter in alphabet]
        print(extra, ''.join(temp))
        return True
    return False


def run2():
    count = 0
    for a, b, c, d, e, f, g, h, i in itertools.permutations((1, 2, 4, 5,  6, 7, 8, 9, 12)):
        count += 1
        grid = (a, 7, 2, b, 2, c, 5, d, 2, 6, e, f, g, h, i, 2)
        if count < 2:
            print(sum(grid))
        if grid[0:4] == grid[4:8] == grid[8:12] == grid[12:16] == 20:
                print(grid)
    print(count)

def main():
    alphabet = 'ihlfrvu'
    for count in range(0, 8):
        for letters in itertools.combinations_with_replacement(alphabet, count):
            run(''.join(letters))


if __name__ == '__main__':
    run(show=True)

