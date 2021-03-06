import itertools
from collections import Counter
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


class ClueInfo(NamedTuple):
    clue: Clue
    evaluator: Evaluator
    unbound_letters: Set[Letter]
    intersections: List[Intersection]
    known_locations: Set[Location]


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
            return predicate(*(self._known_clues[clue] for clue in actual_clues))

        check_relationship.__name__ = name

        self._all_constraints.append((actual_clues, check_relationship))

    def solve(self, *, show_time: bool = True, debug: bool = False, max_debug_depth: Optional[int] = None) -> int:
        self._step_count = 0
        self._solution_count = 0
        self._known_letters = {}
        self._known_clues = {}
        self._debug = debug
        time1 = datetime.now()
        self._solving_order = self._get_solving_order()
        time2 = datetime.now()
        self._solve(0)
        time3 = datetime.now()
        if show_time:
            print(f'Solutions {self._solution_count}; steps: {self._step_count}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; Total: {time3 - time1}')
        return self._solution_count

    def _solve(self, current_index: int) -> None:
        if current_index == len(self._solving_order):
            if self.check_solution(self._known_clues, self._known_letters):
                self.show_solution(self._known_clues, self._known_letters)
                self._solution_count += 1
            return
        clue, evaluator, clue_letters, pattern_maker, constraints = self._solving_order[current_index]
        twin_value = self._known_clues.get(clue, None)  # None if not a twin, twin's value if it is.
        pattern = pattern_maker(self._known_clues)
        if self._debug:
            print(f'{" | " * current_index} {clue.name} letters={clue_letters} pattern="{pattern.pattern}"')
        try:
            for next_letter_values in self.get_letter_values(self._known_letters, clue_letters):
                self._step_count += 1
                for letter, value in zip(clue_letters, next_letter_values):
                    self._known_letters[letter] = value
                clue_value = evaluator(self._known_letters)
                if twin_value:
                    if clue_value != twin_value:
                        continue
                else:
                    if not (clue_value and pattern.fullmatch(clue_value)):
                        continue
                    self._known_clues.pop(clue, None)
                    if not self._allow_duplicates and clue_value in self._known_clues.values():
                        continue
                    self._known_clues[clue] = clue_value
                    if not all(constraint() for constraint in constraints):
                        continue

                if self._debug:
                    print(f'{" | " * current_index} {clue.name} {clue_letters} '
                          f'{next_letter_values} {clue_value} ({clue.length}): -->')

                self._solve(current_index + 1)

        finally:
            for letter in clue_letters:
                self._known_letters.pop(letter, None)
            if not twin_value:
                self._known_clues.pop(clue, None)

    def _get_solving_order(self) -> Sequence[SolvingStep]:
        """Figures out the best order to solve the various clues."""
        result: List[SolvingStep] = []
        # The number of times each letter appears
        letter_count = Counter(letter for clue in self._clue_list
                               for evaluator in clue.evaluators
                               for letter in evaluator.vars)
        not_yet_ordered: Dict[Evaluator, ClueInfo] = {
            evaluator: ClueInfo(clue, evaluator, set(evaluator.vars), [], set())
            for clue in self._clue_list for evaluator in clue.evaluators
        }
        constraints = [(checker, set(clues)) for clues, checker in self._all_constraints]

        def grading_function(clue_info: ClueInfo) -> Sequence[float]:
            letters = frozenset(clue_info.unbound_letters)
            clue_length = clue_info.clue.length
            return (-len(letters),
                    len(clue_info.known_locations) / clue_length, clue_length,
                    unbound_letters_to_clue_count[letters],
                    unbound_letters_to_letter_count[letters])

        while not_yet_ordered:
            unbound_letters_to_clue_count = Counter(frozenset(clueinfo.unbound_letters)
                                                    for clueinfo in not_yet_ordered.values())
            # unbound_letters_to_clue_infos = defaultdict(list)
            # for clue_info in not_yet_ordered.values():
            #     unbound_letters_to_clue_infos[frozenset(clue_info.unbound_letters)].append(clue_info)
            # unbound_letters_to_clue_count = {
            #     letters: len(clue_infos) for letters, clue_infos in unbound_letters_to_clue_infos.items()
            # }
            unbound_letters_to_letter_count = {
                letters: sum(letter_count[letter] for letter in letters)
                for letters in unbound_letters_to_clue_count
            }
            # unbound_letters_to_clue_locations = {
            #     letters: len({location for clue_info in clue_infos for location in clue_info.clue.locations })
            #     for letters, clue_infos in unbound_letters_to_clue_infos.items()
            # }
            # unbound_letters_to_known_clue_locations = {
            #     letters: len({location for clue_info in clue_infos for location in clue_info.known_locations })
            #     for letters, clue_infos in unbound_letters_to_clue_infos.items()
            # }

            # For each set of not-yet-bound letters, determine the total number of letters in those clues
            clue, evaluator, unknown_letters, intersections, _ = max(not_yet_ordered.values(), key=grading_function)
            not_yet_ordered.pop(evaluator)
            pattern = self.make_pattern_generator(clue, intersections)
            for _, clues in constraints:
                clues.discard(clue)
            # Pull out the constraints for which we've now got solutions to all of its clues
            done_constraints = [checker for checker, clues in constraints if not clues]
            constraints = [(checker, clues) for checker, clues in constraints if clues]
            result.append(SolvingStep(clue, evaluator, tuple(sorted(unknown_letters)), pattern, done_constraints))
            for other_clue, _, other_unknown_letters, other_intersections, other_locations in not_yet_ordered.values():
                # Update the remaining not_yet_ordered clues, indicating more known letters and updated intersections
                other_unknown_letters.difference_update(unknown_letters)
                # What intersections does clue create with this new clue?
                new_intersections = Intersection.get_intersections(other_clue, clue)
                other_intersections += new_intersections
                other_locations.update(intersection.get_location() for intersection in new_intersections)
        assert not constraints
        if self._debug:
            for item in result:
                print(item.clue, item.letters)
        return tuple(result)

    def make_pattern_generator(self, clue: Clue, intersections: Sequence[Intersection]) -> \
            Callable[[Dict[Clue, ClueValue]], Pattern[str]]:
        """
        This method takes a clue and the intersections of this clue with other clues whose values are already
        known when we assign a value to this clue.  It returns a function.

        That returned function, when passed a dictionary containing those clues and their actual values, returns a
        regular expression.  This regular expression should be used to determine if a potential value for "clue" is
        legal using pattern.fullmatch(value).  The value should only fully match the pattern if:
           (1) it is the right length,
           (2) it has the right value in the locations specified by the intersections,
           (3) it has a legal value in the locations that are not specified by the intersections, as specified by
                solver.get_allowed_regp()
        Typically, condition #3 is used to prevent a zero from appearing in a location that is the start of a clue.

        By default, we just call Intersection.make_pattern_generator().  But some implementations may override this.
        """
        return Intersection.make_pattern_generator(clue, intersections, self)

    def get_letter_values(self, known_letters: KnownLetterDict, letters: Sequence[str]) -> Iterable[Sequence[int]]:
        """
        Returns the values that can be assigned to the next "count" variables.  We know that we have already assigned
        values to the variables indicated in known_letters.
        """
        count = len(letters)
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
        self.show_letter_values(known_letters)

    @staticmethod
    def show_letter_values(known_letters: KnownLetterDict) -> None:
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

"""
A  B  C  D  E  G  H  I  K  L  M  N  O  R  S  T  U  V  W 
3  10 2  15 6  4  12 8  18 11 19 9  14 5  1  7  16 17 13
S  C  A  G  R  E  T  I  N  B  L  H  W  O  D  U  V  K  M 
1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19
{<Clue 29d>: '343', <Clue 28a>: '639', <Clue 22d>: '1993', <Clue 23d>: '81119',
 <Clue 35a>: '4389', <Clue 11d>: '2519', <Clue 18a>: '18894', <Clue 19d>: '8675', 
 <Clue 21a>: '3198', <Clue 34a>: '653', <Clue 3d>: '711118', <Clue 15a>: '2316',
  <Clue 20d>: '4694', <Clue 14a>: '5151', <Clue 7d>: '19133', <Clue 31a>: '789', 
  <Clue 12a>: '1125', <Clue 27d>: '1983', <Clue 17d>: '33317', <Clue 9d>: '5131', 
  <Clue 32a>: '4311', <Clue 7a>: '1965', <Clue 10a>: '823', <Clue 2d>: '3315', 
  <Clue 25a>: '7318', <Clue 26d>: '1856', <Clue 30a>: '173', <Clue 25d>: '7714', 
  <Clue 4d>: '6210', <Clue 4a>: '6916', <Clue 1d>: '88146', <Clue 16a>: '6193', 
  <Clue 5d>: '9569', <Clue 13a>: '1113', <Clue 8d>: '6116', <Clue 6d>: '16142', 
  <Clue 24d>: '1111', <Clue 33a>: '111417', <Clue 1a>: '81237'}
"""
