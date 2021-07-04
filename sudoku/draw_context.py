from collections import UserDict
from typing import Tuple, Any, Sequence

from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import FancyBboxPatch


class DrawContext(UserDict):
    _axis: Axes

    def __init__(self, axis) -> None:
        super().__init__()
        self._axis = axis

    def draw_circle(self, center: Tuple[float, float], radius: float, **args: Any) -> None:
        self._axis.add_patch(plt.Circle(center, radius=radius, **args))

    def draw_text(self, x: float, y: float, text: str, **args: Any) -> None:
        plt.text(x, y, text, **args)

    def draw_rectangle(self, corner: Tuple[float, float], *, width: float, height: float, **args: Any):
        self._axis.add_patch(
            plt.Rectangle(corner, width=width, height=height, **args))

    def draw_rectangles(self, points: Sequence[Tuple[int, int]], **args: Any):
        args = {'color': 'lightgrey', 'fill': True, **args}
        axis = plt.gca()
        for row, column in points:
            axis.add_patch(plt.Rectangle((column, row), width=1, height=1, **args))

    def draw_line(self, points: Sequence[Tuple[int, int]], *, closed: bool = False, **kwargs: Any) -> None:
        ys = [row + .5 for row, _ in points]
        xs = [column + .5 for _, column in points]
        if closed:
            ys.append(ys[0])
            xs.append(xs[0])
        plt.plot(xs, ys, **{'color': 'black', **kwargs})

    def plot(self, xs, ys, **args: Any):
        plt.plot(xs, ys, **args)

    def arrow(self, x: float, y: float, dx: float, dy: float, **args: Any):
        plt.arrow(x, y, dx, dy, **args)

    def add_fancy_bbox(self, center, width, height, **args: Any):
        self._axis.add_patch(FancyBboxPatch(center, width=width, height=height, **args))
