import itertools
from datetime import datetime
from operator import itemgetter
from typing import Dict, NamedTuple, Sequence, Callable, Pattern, Any, List, Iterable, Set, Tuple

from .base_solver import BaseSolver
from .clue import Clue
from .clue_list import ClueList
from .clue_types import Letter, ClueValue, Location
from .evaluator import Evaluator
from .intersection import Intersection

KnownLetterDict = Dict[Letter, int]
KnownClueDict = Dict[Clue, ClueValue]
ClueInfo = Tuple[Clue, Evaluator, Set[Letter], List[Intersection], Set[Location]]


class SolvingStep(NamedTuple):
    clue: Clue  # The clue we are solving
    evaluator: Evaluator
    letters: Sequence[Letter]  # The letters we are assigning a value in this step
    pattern_maker: Callable[[KnownClueDict], Pattern[str]]  # a pattern maker


class EquationSolver(BaseSolver):
    step_count: int
    solution_count: int
    known_letters: KnownLetterDict
    known_clues: Dict[Clue, ClueValue]
    solving_order: Sequence[SolvingStep]
    items: Sequence[int]
    debug: bool

    def __init__(self, clue_list: ClueList, *, items: Sequence[int] = (), **args: Any) -> None:
        super().__init__(clue_list, **args)
        self.items = items

    def solve(self, *, show_time: bool = True, debug: bool = False) -> int:
        self.step_count = 0
        self.solution_count = 0
        self.known_letters = {}
        self.known_clues = {}
        self.debug = debug
        time1 = datetime.now()
        self.solving_order = self._get_solving_order()
        time2 = datetime.now()
        self.__solve(0)
        time3 = datetime.now()
        if show_time:
            print(f'Solutions {self.solution_count}; steps: {self.step_count}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; Total: {time3 - time1}')
        return self.solution_count

    def __solve(self, current_index: int) -> None:
        if current_index == len(self.solving_order):
            if self.check_solution(self.known_clues, self.known_letters):
                self.show_solution(self.known_clues, self.known_letters)
                self.solution_count += 1
            return
        clue, evaluator, clue_letters, pattern_maker = self.solving_order[current_index]
        twin_value = self.known_clues.get(clue, None)  # None if not a twin, twin's value if it is.
        pattern = pattern_maker(self.known_clues)
        if self.debug:
            print(f'{" | " * current_index} {clue.name} length={clue_letters} pattern="{pattern.pattern}"')

        try:
            for next_letter_values in self.get_letter_values(self.known_letters, len(clue_letters)):
                self.step_count += 1
                for letter, value in zip(clue_letters, next_letter_values):
                    self.known_letters[letter] = value
                clue_value = evaluator(self.known_letters)
                if twin_value:
                    if clue_value != twin_value:
                        continue
                else:
                    if not (clue_value and pattern.match(clue_value)):
                        continue
                    if not self.allow_duplicates and clue_value in self.known_clues.values():
                        continue
                    self.known_clues[clue] = clue_value

                if self.debug:
                    print(f'{" | " * current_index} {clue.name} {clue_letters} '
                          f'{next_letter_values} {clue_value} ({clue.length}): -->')

                self.__solve(current_index + 1)

        finally:
            for letter in clue_letters:
                self.known_letters.pop(letter, None)
            if not twin_value:
                self.known_clues.pop(clue, None)

    def _get_solving_order(self) -> Sequence[SolvingStep]:
        """Figures out the best order to solve the various clues."""
        result: List[SolvingStep] = []
        not_yet_ordered: Dict[Any, ClueInfo] = {
            # co_names are the unbound variables in the compiled expression: exactly what we want!
            evaluator: (clue, evaluator, set(evaluator.vars), [], set())
            for clue in self.clue_list for evaluator in clue.evaluators
        }

        def grading_function(clue_info: ClueInfo) -> Sequence[float]:
            (clue, _, letters, _, locations) = clue_info
            return -len(letters), len(locations) / clue.length, clue.length

        while not_yet_ordered:
            clue, evaluator, unknown_letters, intersections, _ = max(not_yet_ordered.values(), key=grading_function)
            not_yet_ordered.pop(evaluator)
            pattern = Intersection.make_pattern_generator(clue, intersections, self.clue_list)
            result.append(SolvingStep(clue, evaluator, tuple(sorted(unknown_letters)), pattern))
            for other_clue, _, other_unknown_letters, other_intersections, other_locations in not_yet_ordered.values():
                # Update the remaining not_yet_ordered clues, indicating more known letters and updated intersections
                other_unknown_letters.difference_update(unknown_letters)
                # What intersections does clue create with this new clue?
                new_intersections = Intersection.get_intersections(other_clue, clue)
                other_intersections += new_intersections
                other_locations.update(intersection.get_location() for intersection in new_intersections)

        return tuple(result)

    def get_letter_values(self, known_letters: KnownLetterDict, count: int) -> Iterable[Sequence[int]]:
        """
        Returns the values that can be assigned to the next "count" variables.  We know that we have already assigned
        values to the variables indicated in known_letters.
        """
        if count == 0:
            yield ()
            return
        unused_values = (i for i in self.items if i not in set(known_letters.values()))
        yield from itertools.permutations(unused_values, count)

    def get_letter_values_with_duplicates(self, known_letters: KnownLetterDict, count: int, max_per_item: int) -> \
            Iterable[Sequence[int]]:
        if count == 0:
            yield ()
            return
        current_letter_values = tuple(known_letters.values())
        for next_letter_values in itertools.product(self.items, repeat=count):
            if all(current_letter_values.count(value) + next_letter_values.count(value) <= max_per_item
                   for value in next_letter_values):
                yield next_letter_values

    # noinspection PyMethodMayBeStatic
    def check_solution(self, _known_clues: KnownClueDict, _known_letters: KnownLetterDict) -> bool:
        """
        Called when we have a tentative solution.  You should override this method if additional checking
        is required.

        :param _known_clues: A dictionary giving the value of each of the clues.  Clue -> ClueValue
        :param _known_letters: A dictionary giving the value of each equation letter.  Letter -> int
        :return: True if this solution is correct; false otherwise
        """
        return True

    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        self.clue_list.plot_board(known_clues)
        max_length = max(len(str(i)) for i in known_letters.values())
        print()
        pairs = [(letter, value) for letter, value in known_letters.items()]
        pairs.sort()
        print(' '.join(f'{letter:<{max_length}}' for letter, _ in pairs))
        print(' '.join(f'{value:<{max_length}}' for _, value in pairs))
        print()
        pairs.sort(key=itemgetter(1))
        print(' '.join(f'{letter:<{max_length}}' for letter, _ in pairs))
        print(' '.join(f'{value:<{max_length}}' for _, value in pairs))
