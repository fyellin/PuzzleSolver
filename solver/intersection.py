from __future__ import annotations

import re
from typing import NamedTuple, Sequence, Callable, Dict, Pattern, List, Optional

from .base_solver import BaseSolver
from .clue import Clue
from .clue_types import Location, ClueValue


class Intersection(NamedTuple):
    this_clue: Clue
    this_index: int
    other_clue: Clue
    other_index: int

    def get_location(self) -> Location:
        """Returns the location of this intersection"""
        return self.this_clue.locations[self.this_index]


    @staticmethod
    def get_intersections(this: Clue, other: Clue) -> Sequence[Intersection]:
        """
        Returns the intersection(s) of the two clue arguments.  The resulting intersection(s) all have
        the first argument as "this_clue" and the second argument as "other_clue".
        """
        clashes = this.location_set.intersection(other.location_set)
        return tuple(Intersection(this, this.locations.index(clash), other, other.locations.index(clash))
                     for clash in clashes)

    def values_match(self, this_value: ClueValue, other_value: ClueValue) -> bool:
        """
        Returns true if setting the this_clue and other_clue to this_value and other_value would give a match
        at this intersection of those two clues.
        """
        return this_value[self.this_index] == other_value[self.other_index]

    @staticmethod
    def make_pattern_generator(clue: Clue, intersections: Sequence[Intersection], solver: BaseSolver) -> \
            Callable[[Dict[Clue, ClueValue]], Pattern[str]]:
        """
        This function takes a clue and the intersections of this clue with other clues whose values are already
        known when we assign a value to this clue.  It returns a function.

        That returned function, when passed a dictionary containing the actual values of those clues, returns a
        regular expression.  This regular expression is used to determine if a potential value for "clue" matches.
        It should only match if (1) it is the right length, (2) it has the right value in the specified intersections,
        and (3) it matches the regexp specified by solver.get_allowed_regexp() for those locations that aren't one
        of the specified intersections.  Typically, (3) is used to prevent a zero from appearing in a location that is
        the start of a clue.
        """
        pattern_list = [solver.get_allowed_regexp(location) for location in clue.locations]
        pattern_list.append('$')

        if not intersections:
            # There are no intersections.  We just return a function that generates our pattern.
            pattern = re.compile(''.join(pattern_list))
            return lambda _: pattern

        assert(all(intersection.this_clue == clue for intersection in intersections))

        # {0}, {1}, etc represent the order the items appear in the  "intersections" argument, not necessarily
        # the order that they appear in the pattern.  format can handle that.
        seen_list: List[Optional[Intersection]] = [None] * clue.length
        # If two intersections both refer to the same square, we record them in crashes.
        crashes: List[Intersection] = []
        for i, intersection in enumerate(intersections):
            square_seen_already = seen_list[intersection.this_index]
            if not square_seen_already:
                pattern_list[intersection.this_index] = f'{{{i}:s}}'
                seen_list[intersection.this_index] = intersection
            else:
                one_crash = Intersection(intersection.other_clue, intersection.other_index,
                                         square_seen_already.other_clue, square_seen_already.other_index)
                crashes.append(one_crash)

        pattern_format = ''.join(pattern_list)

        def getter(known_clues: Dict[Clue, ClueValue]) -> Pattern[str]:
            for (clue1, clue1_index, clue2, clue2_index) in crashes:
                assert known_clues[clue1][clue1_index] == known_clues[clue2][clue2_index]
            args = (known_clues[x.other_clue][x.other_index] for x in intersections)
            regexp = pattern_format.format(*args)
            return re.compile(regexp)

        return getter

    def __str__(self) -> str:
        return f'<{self.this_clue.name}[{self.this_index}]={self.other_clue.name}[{self.other_index}] ' \
            f'@ {self.get_location()}>'

    def __repr__(self) -> str:
        return str(self)
