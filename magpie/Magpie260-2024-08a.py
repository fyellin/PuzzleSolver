import numpy as np
from itertools import product

WORDS = """
ROOTSYPSHOOLE
DIGITSUBORNED
WAGEDCREPETPI
ACEROUSAPIOLS
RADICLEFYNOAH
ECRISPERPANTO
MAAEDEFOUNDER
EONPEDALLINGS
NPBIBLICISTLE
WARSTSNREATAW
CREOSOTESMESH
HARDPANSTOUSE
ANTEOPATENTOR
"""

def get_grid():
    lines = WORDS.splitlines()
    lines = [line.strip() for line in lines]
    line = ''.join(lines)
    info = np.array(list(line)).reshape(13, 13)
    return info

def get_words():
    with open("/users/fy/Pycharm/MagpieSolver/misc/words.txt") as file:
        words = file.readlines()
        words = {word.strip().upper().replace(" ", "") for word in words}
    return words

def main():
    grid = get_grid()
    words = get_words()
    columns = (2, 4, 6, 8, 10)
    pos_offsets = (6, 4, 6, 2, 6)
    neg_offsets = tuple(13 - x for x in pos_offsets)
    for rotations in product(*zip(pos_offsets, neg_offsets)):
        copy = grid.copy()
        for column, rotation in zip(columns, rotations):
            copy[0:rotation, column] = grid[-rotation:, column]
            copy[rotation:, column] = grid[0:-rotation, column]
        temp = [''.join(copy[i]) for i in range(13)]
        possibles = [temp[i][j:k] for i in range(13) for j in range(13) for k in range(j + 5, 13)]
        possibles = [x for x in possibles if x in words]
        print(rotations)
        print(temp)
        print(possibles)



if __name__ == '__main__':
    main()
