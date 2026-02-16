import itertools
import multiprocessing
import pickle
import re
from collections import Counter
from collections.abc import Iterable, Callable, Sequence
from datetime import datetime
from operator import itemgetter
from typing import Any, NamedTuple

from .base_solver import BaseSolver, KnownClueDict
from .clue import Clue
from .clue_types import ClueValue, Letter, Location
from .evaluator import Evaluator
from .intersection import Intersection

type KnownLetterDict = dict[Letter, int]


class ClueInfo(NamedTuple):
    clue: Clue
    evaluator: Evaluator
    unbound_letters: set[Letter]
    intersections: list[Intersection]
    known_locations: set[Location]


class SolvingStep(NamedTuple):
    clue: Clue  # The clue we are solving
    evaluator: Evaluator
    letters: Sequence[Letter]  # The letters we are assigning a value in this step
    pattern_maker: Callable[[KnownClueDict], re.Pattern[str]]  # a pattern maker
    constraints: Sequence[Callable[[], bool]]


class EquationSolver(BaseSolver):
    _step_count: int
    _solutions: list[tuple[KnownClueDict, KnownLetterDict]]
    _known_letters: KnownLetterDict
    _known_clues: KnownClueDict
    _solving_order: Sequence[SolvingStep]
    _items: Sequence[int]
    _all_constraints: list[tuple[tuple[Clue, ...], Callable[[], bool]]]
    _debug: bool
    _max_debug_depth: int

    def __init__(self, clue_list: Sequence[Clue], *, items: Iterable[int] = (), **args: Any) -> None:
        super().__init__(clue_list, **args)
        self._items = tuple(items)
        self._all_constraints = []
        Clue.set_pickle_solver(self)

    def add_constraint(self, clues: Sequence[Clue | str], predicate: Callable[..., bool], *,
                       name: str | None = None) -> None:
        if isinstance(clues, str):
            clues = clues.split()
        assert len(clues) >= 1
        actual_clues = tuple(clue if isinstance(clue, Clue) else self.clue_named(clue) for clue in clues)
        if not name:
            name = '_'.join(clue.name for clue in actual_clues)

        def check_relationship(known_clues = None) -> bool:
            if known_clues is None:
                known_clues = self._known_clues
            return predicate(*(known_clues[clue] for clue in actual_clues))

        check_relationship.__name__ = name

        self._all_constraints.append((actual_clues, check_relationship))

    def solve(self, *, show_time: bool = True, debug: bool = False,
              max_debug_depth: int = 1000, multiprocessing: bool = False):
        self._step_count = 0
        self._solutions = []
        self._known_letters = {}
        self._known_clues = {}
        self._debug = debug
        self._max_debug_depth = -1 if not debug else max_debug_depth
        time1 = datetime.now()
        self._solving_order = self._get_solving_order()
        time2 = datetime.now()
        if multiprocessing:
            self._solve_mp(0)
        else:
            self._solve(0)
        time3 = datetime.now()
        if show_time:
            print(f'Solutions {len(self._solutions)}; steps: {self._step_count}; '
                  f'Setup: {time2 - time1}; Execution: {time3 - time2}; Total: {time3 - time1}')
        return self._solutions

    def _solve(self, current_index: int) -> None:
        if current_index == len(self._solving_order):
            if self.check_solution(self._known_clues, self._known_letters):
                self.show_solution(self._known_clues, self._known_letters)
                self._solutions.append((self._known_clues.copy(), self._known_letters.copy()))
            return
        clue, evaluator, clue_letters, pattern_maker, constraints = self._solving_order[current_index]
        twin_value = self._known_clues.get(clue, None)  # None if not a twin, twin's value if it is.
        pattern = pattern_maker(self._known_clues)
        if current_index < self._max_debug_depth:
            print(f'{" | " * current_index} {clue.name} letters={clue_letters} pattern="{pattern.pattern}"')
        try:
            for next_letter_values in self.get_letter_values(self._known_letters, clue_letters):
                self._step_count += 1
                for letter, value in zip(clue_letters, next_letter_values):
                    self._known_letters[letter] = value
                clue_values = evaluator(self._known_letters)
                if twin_value:
                    if twin_value not in clue_values:
                        continue
                    if current_index <= self._max_debug_depth:
                        print(f'{" | " * current_index} {clue.name} TWIN {clue_letters} '
                              f'{next_letter_values} {twin_value} ({clue.length}): -->')
                    self._solve(current_index + 1)
                    continue
                for clue_value in clue_values:
                    if not (clue_value and pattern.fullmatch(clue_value)):
                        continue
                    self._known_clues.pop(clue, None)
                    if not self._allow_duplicates and clue_value in self._known_clues.values():
                        continue
                    self._known_clues[clue] = clue_value
                    bad_constraint = next((constraint for constraint in constraints if not constraint()), None)
                    if bad_constraint:
                        # print(f'{" | " * current_index} {clue.name} {"".join(clue_letters)} '
                        #       f'{next_letter_values} {clue_value} ({clue.length}): --> X {bad_constraint.__name__}')
                        continue
                    if current_index <= self._max_debug_depth:
                        print(f'{" | " * current_index} {clue.name} {"".join(clue_letters)} '
                              f'{next_letter_values} {clue_value} ({clue.length}): -->')
                    self._solve(current_index + 1)

        finally:
            for letter in clue_letters:
                self._known_letters.pop(letter, None)
            if not twin_value:
                self._known_clues.pop(clue, None)

    def _solve_mp(self, current_index: int) -> None:
        assert current_index < len(self._solving_order)
        clue, evaluator, clue_letters, pattern_maker, constraints = self._solving_order[current_index]
        twin_value = self._known_clues.get(clue, None)  # None if not a twin, twin's value if it is.
        assert twin_value is None
        pattern = pattern_maker(self._known_clues)
        if current_index < self._max_debug_depth:
            print(f'{" | " * current_index} {clue.name} letters={clue_letters} pattern="{pattern.pattern}"')

        items = []
        for next_letter_values in self.get_letter_values(self._known_letters, clue_letters):
            self._known_letters.update(zip(clue_letters, next_letter_values))
            clue_values = evaluator(self._known_letters)
            for clue_value in clue_values:
                if not (clue_value and pattern.fullmatch(clue_value)):
                    continue
                self._known_clues.pop(clue, None)
                if not self._allow_duplicates and clue_value in self._known_clues.values():
                    continue
                self._known_clues[clue] = clue_value
                if not all(constraint() for constraint in constraints):
                    continue
                if current_index <= self._max_debug_depth:
                    print(f'{" | " * current_index} {clue.name} {"".join(clue_letters)} '
                          f'{next_letter_values} {clue_value} ({clue.length}): -->')
                items.append((clue_value, *next_letter_values))
        if len(items) == 0:
            raise Exception("Unexpected lack of qualified items")
        elif len(items) == 1:
            self._solve_mp(current_index + 1)
        else:
            known_clues = self._known_clues
            known_letters = self._known_letters
            args = [(id, type(self), current_index,
                     pickle.dumps(known_clues | {clue: clue_value}),
                     known_letters | dict(zip(clue_letters, letter_values)))
                    for id, (clue_value, *letter_values) in enumerate(items)]
            seen = set(id for id, *_ in args)
            print(f'There are {len(args)} processes')
            max_id = 0
            with multiprocessing.Pool() as pool:
                results =  pool.imap_unordered(self._mp_bridge, args)
                for (id, solutions) in results:
                    seen.remove(id)
                    max_id = max(max_id, id)
                    clue_value, *letter_values = items[id]
                    unfinished_ids = sorted(x for x in seen if x < max_id)
                    unfinished_letters = [items[id][1:] for id in unfinished_ids]
                    print(f'{id} {clue.name} {"".join(clue_letters)} '
                          f'{letter_values} {clue_value} ({clue.length}): --> {len(solutions)} {unfinished_letters} {len(seen)}')
                    for clue_values, letter_values in solutions:
                        self._solutions.append((clue_values, letter_values))

    @staticmethod
    def _mp_bridge(arg):
        id, mytype, current_index, pickled_known_clues, known_letters = arg
        self = mytype()
        # known_clues can't be unpickled until we call Clue.set_pickle_solver.
        Clue.set_pickle_solver(self)
        known_clues = pickle.loads(pickled_known_clues)
        return self._handle_multiprocessing(id, current_index, known_clues, known_letters)

    def _handle_multiprocessing(self, id, current_index, known_clues, known_letters):
        self._step_count = 0
        self._solutions = []

        self._known_letters = known_letters
        self._known_clues = known_clues
        self._debug = False
        self._max_debug_depth = -1
        self._solving_order = self._get_solving_order()
        for i in range(current_index + 1):
            clue, *_ = self._solving_order[i]
            assert clue in self._known_clues
        self._solve(current_index + 1)
        return id, [(known_clues, known_letters)
                    for known_clues, known_letters in self._solutions]

    def _get_solving_order(self) -> Sequence[SolvingStep]:
        """Figures out the best order to solve the various clues."""
        result: list[SolvingStep] = []
        # The number of times each letter appears
        letter_count = Counter(letter for clue in self._clue_list
                               for evaluator in clue.evaluators
                               for letter in evaluator.vars)
        not_yet_ordered: dict[Evaluator, ClueInfo] = {
            evaluator: ClueInfo(clue, evaluator, set(evaluator.vars), [], set())
            for clue in self._clue_list for evaluator in clue.evaluators
        }
        constraints = [(checker, set(clues)) for clues, checker in self._all_constraints]

        def grading_function(clue_info: ClueInfo) -> Sequence[float]:
            letters = frozenset(clue_info.unbound_letters)
            clue_length = clue_info.clue.length
            return (clue_info.clue.priority,
                    -len(letters),
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
            Callable[[KnownClueDict], re.Pattern[str]]:
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
        known_letters = set(known_letters.values())
        unused_values = [i for i in self._items if i not in known_letters]
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
        """
        return True

    # noinspection PyMethodMayBeStatic
    def show_solution(self, known_clues: KnownClueDict, known_letters: KnownLetterDict) -> None:
        self.show_letter_values(known_letters)
        self.plot_board(known_clues, known_letters=known_letters)

    def show_letter_values(self, known_letters: KnownLetterDict) -> None:
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
