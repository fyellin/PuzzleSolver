import itertools
from datetime import datetime
from operator import itemgetter
from typing import Dict, NamedTuple, Sequence, Callable, Pattern, Any, List, Iterable, Set, Tuple, Union, Optional

from .base_solver import BaseSolver
from .clue import Clue
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
    constraints: Sequence[Callable[[], bool]]


class EquationSolver(BaseSolver):
    _step_count: int
    _solution_count: int
    _known_letters: KnownLetterDict
    _known_clues: Dict[Clue, ClueValue]
    _solving_order: Sequence[SolvingStep]
    _items: Sequence[int]
    _all_constraints: List[Tuple[Tuple[Clue, ...], Callable[[], bool]]]
    _debug: bool

    def __init__(self, clue_list: Sequence[Clue], *, items: Iterable[int] = (), **args: Any) -> None:
        super().__init__(clue_list, **args)
        self._items = tuple(items)
        self._all_constraints = []

    def add_constraint(self, clues: Sequence[Union[Clue, str]], predicate: Callable[..., bool], *,
                       name: Optional[str] = None) -> None:
        assert len(clues) >= 1
        actual_clues = tuple(clue if isinstance(clue, Clue) else self.clue_named(clue) for clue in clues)
        if not name:
            name = '_'.join(clue.name for clue in actual_clues)

        def check_relationship() -> bool:
            values = [self._known_clues[clue] for clue in actual_clues]
            return predicate(*(self._known_clues[clue] for clue in actual_clues))

        check_relationship.__name__ = name

        self._all_constraints.append((actual_clues, check_relationship))

    def solve(self, *, show_time: bool = True, debug: bool = False) -> int:
        self._step_count = 0
        self._solution_count = 0
        self._known_letters = {}
        self._known_clues = {}
        self._debug = debug
        time1 = datetime.now()
        self._solving_order = self._get_solving_order()
        time2 = datetime.now()
        self.__solve(0)
        time3 = datetime.now()
        if show_time:
            print(f'Solutions {self._solution_count}; steps: {self._step_count}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; Total: {time3 - time1}')
        return self._solution_count

    def __solve(self, current_index: int) -> None:
        if current_index == len(self._solving_order):
            if self.check_solution(self._known_clues, self._known_letters):
                self.show_solution(self._known_clues, self._known_letters)
                self._solution_count += 1
            return
        clue, evaluator, clue_letters, pattern_maker, constraints = self._solving_order[current_index]
        twin_value = self._known_clues.get(clue, None)  # None if not a twin, twin's value if it is.
        pattern = pattern_maker(self._known_clues)
        if self._debug:
            print(f'{" | " * current_index} {clue.name} length={clue_letters} pattern="{pattern.pattern}"')

        try:
            for next_letter_values in self.get_letter_values(self._known_letters, len(clue_letters)):
                self._step_count += 1
                for letter, value in zip(clue_letters, next_letter_values):
                    self._known_letters[letter] = value
                clue_value = evaluator(self._known_letters)
                if twin_value:
                    if clue_value != twin_value:
                        continue
                else:
                    if not (clue_value and pattern.match(clue_value)):
                        continue
                    if not self._allow_duplicates and clue_value in self._known_clues.values():
                        continue
                    self._known_clues[clue] = clue_value
                    if not all(constraint() for constraint in constraints):
                        continue

                if self._debug:
                    print(f'{" | " * current_index} {clue.name} {clue_letters} '
                          f'{next_letter_values} {clue_value} ({clue.length}): -->')

                self.__solve(current_index + 1)

        finally:
            for letter in clue_letters:
                self._known_letters.pop(letter, None)
            if not twin_value:
                self._known_clues.pop(clue, None)

    def _get_solving_order(self) -> Sequence[SolvingStep]:
        """Figures out the best order to solve the various clues."""
        result: List[SolvingStep] = []
        not_yet_ordered: Dict[Any, ClueInfo] = {
            # co_names are the unbound variables in the compiled expression: exactly what we want!
            evaluator: (clue, evaluator, set(evaluator.vars), [], set())
            for clue in self._clue_list for evaluator in clue.evaluators
        }
        constraints = [(callable, set(clues)) for clues, callable in self._all_constraints]

        def grading_function(clue_info: ClueInfo) -> Sequence[float]:
            (clue, _, letters, _, locations) = clue_info
            return -len(letters), len(locations) / clue.length, clue.length

        while not_yet_ordered:
            clue, evaluator, unknown_letters, intersections, _ = max(not_yet_ordered.values(), key=grading_function)
            not_yet_ordered.pop(evaluator)
            pattern = Intersection.make_pattern_generator(clue, intersections, self)
            for _, clues in constraints:
                clues.discard(clue)
            # Pull out the constraints that we've now got solutions to all of its clues.
            done_constraints = [callable for callable, clues in constraints if not clues]
            constraints = [(callable, clues) for callable, clues in constraints if clues]
            result.append(SolvingStep(clue, evaluator, tuple(sorted(unknown_letters)), pattern, done_constraints))
            for other_clue, _, other_unknown_letters, other_intersections, other_locations in not_yet_ordered.values():
                # Update the remaining not_yet_ordered clues, indicating more known letters and updated intersections
                other_unknown_letters.difference_update(unknown_letters)
                # What intersections does clue create with this new clue?
                new_intersections = Intersection.get_intersections(other_clue, clue)
                other_intersections += new_intersections
                other_locations.update(intersection.get_location() for intersection in new_intersections)
        assert not constraints
        return tuple(result)

    def get_letter_values(self, known_letters: KnownLetterDict, count: int) -> Iterable[Sequence[int]]:
        """
        Returns the values that can be assigned to the next "count" variables.  We know that we have already assigned
        values to the variables indicated in known_letters.
        """
        if count == 0:
            yield ()
            return
        unused_values = (i for i in self._items if i not in set(known_letters.values()))
        yield from itertools.permutations(unused_values, count)

    def get_letter_values_with_duplicates(self, known_letters: KnownLetterDict, count: int, max_per_item: int) -> \
            Iterable[Sequence[int]]:
        if count == 0:
            yield ()
            return
        current_letter_values = tuple(known_letters.values())
        for next_letter_values in itertools.product(self._items, repeat=count):
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
        self.plot_board(known_clues)
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
