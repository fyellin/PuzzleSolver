import itertools
from typing import Sequence, Set, Dict, Any

import math
from matplotlib import pyplot as plt

WORDS = """
HATBRUSH
SAUGERS
SAVANTS
OVENWARE
PHYLARCH
ALRIGHT
LAVABOS
GALATEA
YARDAGE
HORMONIC
HARBOUR
TWELFTH
FERVENT
FRISETTE
FRIESIC
ISOGAMY
OUREBIS
FRISSON
IMAGINE
NUTARIAN
BULLHORN
ORSEILLE
THROTTLER
OAR FISH
MOONSHEE
WORKSHY
RHACHIS
CHARPOY
PREWARM
IMPROVE
AT THE TIME
DISHOME
ERITREA
TRANGAM
TRIENNIA
TURGENT
LEADOUT"""

EXTRAS = "HAVEHAVEYOUEVERGONEALLTHEWAYWITHAGIRL"

RING1 =  "ASSOCIATECATERCOUSINBELAMYCOMRADEMATE"
RING3 =  "BENNYHOGANBLESSMEFATHERFORIHAVESINNED"


def get_words():
    assert len(EXTRAS) == 37
    words = WORDS.strip().splitlines()
    assert len(words) == 37
    words2 = [word.replace(' ', '').replace(extra, '') for word, extra in zip(words, EXTRAS)]
    for word in words2:
        assert len(word) == 6

    words3 = []
    for word, ring1, ring3 in zip(words2, RING1, RING3):
        possibilities = [(word[i:] + word[:i]) for i in range(0, 6)] + [word[::-1]]
        possibilities = [x for x in possibilities if x[0] == ring1 and x[2] == ring3]
        if len(possibilities) == 2:
            possibilities.pop(0)
        words3.append(possibilities[0])
    return words3


def draw_grid():
        figure, axes = plt.subplots(1, 1, figsize=(8, 8), dpi=100)

        # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
        axes.axis([-8, 8, -8, 8])
        axes.axis('equal')
        axes.axis('off')
        figure.tight_layout()
        for radius in range(2, 9):
            axes.add_patch(plt.Circle((0, 0), radius, fill=False))

        words = get_words()

        def cossin(i):
            temp = .25 - i / 37.0
            angle = temp * 2 * math.pi
            return math.cos(angle), math.sin(angle),  -i * 360 / 37

        for i in range(0, 37):
            cos, sin, _ = cossin(i)
            plt.plot((4 * cos, 8 * cos), (4 * sin, 8 * sin), color='black')
            if i in range(0, 36, 3):
                plt.plot((2 * cos, 3 * cos), (2 * sin, 3 * sin), color='black')
            if i in range(2, 37, 3):
                plt.plot((3 * cos, 4 * cos), (3 * sin, 4 * sin), color='black')

            cos, sin, _ = cossin(i + .2)
            plt.text(7.8 * cos, 7.8 * sin, str(i + 1),
                     verticalalignment='center', horizontalalignment='center')
            if i+1 in (4, 7, 19, 28, 31, 36):
                plt.text(6.8 * cos, 6.8 * sin, '*',
                         verticalalignment='center', horizontalalignment='center', fontweight='bold')

        for letter_index in range(0, 6):
            radius = 7.5 - letter_index
            if 0 <= letter_index <= 3:
                for i in range(0, 37):
                    letter = words[i][letter_index]
                    cos, sin, rotation = cossin(i + .5)
                    plt.text(radius * cos, radius * sin, letter,
                             verticalalignment='center', horizontalalignment='center', fontsize=15, fontweight='bold')
            elif letter_index == 4:
                for i in range(0, 36, 3):
                    letter = words[i][letter_index]
                    cos, sin, rotation = cossin(i + .5)
                    plt.text(radius * cos, radius * sin, letter,
                             verticalalignment='center', horizontalalignment='center', fontsize=15, fontweight='bold')
            elif letter_index == 5:
                for i in range(2, 37, 3):
                    letter = words[i][letter_index]
                    cos, sin, rotation = cossin(i)
                    plt.text(radius * cos, radius * sin, letter,
                             verticalalignment='center', horizontalalignment='center', fontsize=15, fontweight='bold')


        plt.text(0, 0, "Maeve\nBinchy".upper(), verticalalignment='center', horizontalalignment='center',
                 fontweight='bold', fontsize=20)

        plt.show()


if __name__ == '__main__':
    draw_grid()

