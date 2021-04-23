import cmath
import itertools
import math

import matplotlib as mpl
from matplotlib import pyplot as plt
from scipy.interpolate import CubicSpline

ROWS = (
    "ASESCRAMSPOORSOSCARUNE",
    "GENPANDAHOUSEINCOPENHA",
    "EATINWORRITCIGARBEDLAM",
    "NTINUENIUSCUtIGERMDECO",
    "DEVELXINGERLEVEEMAOSUN",
    "ADELAPSESTYERERNINGSEN"
)


def draw_grid():
    figure, axes = plt.subplots(1, 1, figsize=(8, 8), dpi=100)

    # Set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
    axes.axis([-8, 8, -8, 8])
    axes.axis('equal')
    axes.axis('off')
    figure.tight_layout()
    mpl.rcParams['savefig.pad_inches'] = 0


    # args = dict(color="black", width=6, height=8, theta1=90, theta2=270, linewidth=2, alpha=.4)
    # axes.add_patch(Arc(xy=(0, 4), angle=90, **args))
    # axes.add_patch(Arc(xy=(0, -4), angle=180, **args))

    def cossin(i):
        temp = .25 - i / 22.0
        angle = temp * 2 * math.pi
        return math.cos(angle), math.sin(angle),  -i * 360 / 22

    # angle = 130
    # x, y = math.cos(angle * 2 * math.pi / 360), math.sin(angle * 2 * math.pi / 360)
    #
    # axes.add_patch(Wedge(center=(0, 0), r=8, theta1=angle + 180, theta2=angle, fc='lightgray'))
    # axes.add_patch(Wedge(center=(4 * x, 4 * y), r=4, theta1=angle, theta2=angle + 180, fc='lightgray'))
    # axes.add_patch(Wedge(center=(-4 * x, -4 * y), r=4, theta1=angle + 180, theta2=angle, fc='white'))

    # args = dict(color="black", width=8.0, height=8, theta1=90, theta2=270, linewidth=2, alpha=.4)
    # axes.add_patch(Arc(xy=(4 * x, 4 * y), angle=angle + 90, **args))
    # axes.add_patch(Arc(xy=(-4 * x, -4 * y), angle=angle + 270, **args))

    def foo(x, r):
        angle = math.radians(90 - x * (360 / 22.0))
        return r * cmath.exp(angle * 1j)

    import numpy as np
    points = np.array([foo(-2, 7.5), foo(-1, 7.5), foo(0, 6.5),   # N E G
                       foo(1, 5.5), foo(1.3, 4.8), foo(1.8, 4.2),   # A T O
                       foo(2, 3.5), foo(2, 1.5), foo(2, .5), foo(2, 0)])
    # plt.plot(points.real, points.imag, color='black')
    # plt.plot(-points.real, -points.imag, color='black')

    cs = CubicSpline(list(range(len(points))), points)
    xs = np.linspace(0, len(points) - 1, 100)
    ys = cs(xs)
    plt.plot(ys.real, ys.imag, color='red', linewidth=8, alpha=.4)
    plt.plot(-ys.real, -ys.imag, color='red', linewidth=8, alpha=.4)







    for radius in range(2, 8 + 1):
        width = 1
        axes.add_patch(plt.Circle((0, 0), radius, fill=False, linewidth=width))

    for i in range(0, 22):
        cos, sin, _ = cossin(i + .5)
        plt.plot((2 * cos, 8 * cos), (2 * sin, 8 * sin), color='black')

    for ring, letters in enumerate(ROWS, start=1):
        for square, letter in enumerate(letters):
            cos, sin, angle = cossin(square)
            t = plt.text((8.5 - ring) * cos, (8.5 - ring) * sin, letter.upper(),
                     verticalalignment='center', horizontalalignment='center',
                     rotation=angle,
                     fontweight='bold', fontsize=15)

    for x, y in itertools.product((-8.1, 8.1), repeat=2):
        axes.add_patch(plt.Circle((x, y), .05, fill=True, linewidth=width))

    plt.show()

if __name__ == '__main__':
        draw_grid()
