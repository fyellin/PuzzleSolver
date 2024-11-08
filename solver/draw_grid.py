from collections.abc import Sequence, Callable
from typing import Any, cast, Optional
from itertools import product

from matplotlib import pyplot as plt, patches
from matplotlib.axes import Axes

from .clue_types import Location


def draw_grid(*, max_row: int, max_column: int,
              clued_locations: Optional[set[Location]] = None,
              location_to_entry: dict[Location, str] = None,
              location_to_clue_numbers: dict[Location, Sequence[str]] = None,
              top_bars: set[Location] = frozenset(),
              left_bars: set[Location] = frozenset(),
              shading: dict[Location, str] = None,
              coloring: dict[Location, str] = None,
              rotation: dict[Location, str] = None,
              circles: set[Location] = frozenset(),
              subtext: Optional[str] = None,
              font_multiplier: float = 1.0,
              blacken_unused: bool = True,
              file: Optional[str] = None,
              grid_drawer: Callable[[plt, Axes], None] = None,
              extra: Callable[[plt, Axes], None] = None,
              **args: Any) -> None:

    _axes = args.get('axes')
    if _axes:
        axes = cast(Axes, _axes)
    else:
        _, axes = plt.subplots(1, 1, figsize=(8, 11), dpi=100)

    # set (1,1) as the top-left corner, and (max_column, max_row) as the bottom right.
    axes.axis([1, max_column, max_row, 1])
    axes.axis('equal')
    axes.axis('off')

    if clued_locations is None:
        clued_locations = set(product(range(1, max_row), range(1, max_column)))
    if shading is None:
        shading = {}
    if rotation is None:
        rotation = {}
    if location_to_clue_numbers is None:
        location_to_clue_numbers = {}
    if location_to_entry is None:
        location_to_entry = {}
    if coloring is None:
        coloring = {}

    # Fill in the shaded squares
    for row, column in product(range(1, max_row), range(1, max_column)):
        if (row, column) in shading:
            color = shading[row, column]
            axes.add_patch(patches.Rectangle((column, row), 1, 1,
                                             facecolor=color, linewidth=0))
        elif (row, column) not in clued_locations:
            if blacken_unused:
                axes.add_patch(patches.Rectangle((column, row), 1, 1,
                                                 facecolor='black', linewidth=0))

    if grid_drawer is None:
        for row, column in product(range(1, max_row + 1), range(1, max_column + 1)):
            this_exists = (row, column) in clued_locations
            left_exists = (row, column - 1) in clued_locations
            above_exists = (row - 1, column) in clued_locations
            if this_exists or left_exists:
                width = (5 if this_exists != left_exists or (row, column) in left_bars
                         else None)
                axes.plot([column, column], [row, row + 1], 'black', linewidth=width)
            if this_exists or above_exists:
                width = (5 if this_exists != above_exists or (row, column) in top_bars
                         else None)
                axes.plot([column, column + 1], [row, row], 'black', linewidth=width)

    else:
        grid_drawer(plt, axes)

    for row, column in circles:
        circle = plt.Circle((column + .5, row + .5),
                            radius=.4, linewidth=2, fill=False, facecolor='black')
        axes.add_patch(circle)

    points_per_data = 60 * font_multiplier

    # Fill in the values
    for (row, column), entry in location_to_entry.items():
        color = coloring.get((row, column), 'black')
        axes.text(column + 1 / 2, row + 1 / 2, entry,
                  color=color,
                  fontsize=points_per_data / 2, fontweight='bold', fontfamily="SF Pro Text",
                  va='center', ha='center', rotation=rotation.get((row, column), 0))

    if subtext is not None:
        axes.text((max_column + 1) / 2, max_row + .1, subtext,
                  fontsize=points_per_data / 2, fontweight='bold',
                  fontfamily="sans-serif", va='top', ha='center')

    # Fill in the clue numbers
    for (row, column), clue_numbers in location_to_clue_numbers.items():
        font_info = dict(fontsize=points_per_data / 4, fontfamily="sans-serif")
        for index, text in enumerate(clue_numbers):
            if index == 0:
                axes.text(column + .05, row + .05, text,
                          va='top', ha='left', **font_info)
            elif index == 1:
                axes.text(column + .95, row + .05, text,
                          va='top', ha='right', **font_info)
            elif index == 2:
                axes.text(column + .05, row + .95, text,
                          va='bottom', ha='left', **font_info)
            elif index == 3:
                axes.text(column + .95, row + .95, text,
                          va='bottom', ha='right', **font_info)

    if extra:
        extra(plt, axes)

    if file is not None:
        plt.savefig(file)

    if not _axes:
        plt.show()
