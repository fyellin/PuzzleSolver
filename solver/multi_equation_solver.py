import cProfile
import glob
import itertools
import multiprocessing
import os
import pstats
import queue
from collections import deque
from collections.abc import Sequence

from . import Clue
from .clue_types import ClueValue, Letter
from .base_solver import KnownClueDict
from .equation_solver import EquationSolver, KnownLetterDict
from .mytaskqueue import MyTaskQueue

State = tuple[KnownClueDict, KnownLetterDict]

REAL_MULTIPROCESSING = True

MAX_LOCAL_QUEUE_SIZE = 40
RUN_PROFILER = True
TASK_QUEUE_SIZE = 1_000_000_000


class MultiEquationSolver(EquationSolver):
    ordered_clues: Sequence[Clue]
    ordered_variables: Sequence[Letter]

    def __init__(self, *args,  task_queue_size=TASK_QUEUE_SIZE, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_queue_size = task_queue_size
        self._debug = False
        Clue.set_pickle_solver(self)

    def _solve(self, _):
        result_queue = multiprocessing.Queue()
        cpu_count = os.cpu_count()

        task_queue = MyTaskQueue(size=self.task_queue_size)
        task_queue.put((0, [[{}, {}]]))
        if REAL_MULTIPROCESSING:
            workers = [Worker(type(self), task_queue, result_queue, id=i + 1)
                       for i in range(cpu_count)]
            for worker in workers:
                worker.start()

            task_queue.join()

            for _ in workers:
                task_queue.put(None)
            for worker in workers:
                worker.join()
        else:
            worker = Worker(type(self), task_queue, result_queue, id=1)
            worker.run()

        task_queue.close(True)

        while not result_queue.empty():
            result = result_queue.get()
            self.show_solution(*result)
            self._solutions.append(result)

        if RUN_PROFILER:
            stats = pstats.Stats()
            stats.add(*glob.glob("/tmp/solver*"))
            stats.sort_stats('time').print_stats(30)

    _solve_mp = _solve

    def _inner_solve(self, current_index: int, states: Sequence[State]
                     ) -> Sequence[tuple[KnownClueDict, ClueValue,
                                   KnownLetterDict, Sequence[int]]]:
        if current_index == len(self._solving_order):
            results = [(known_clues, ClueValue(''), known_letters, ())
                       for known_clues, known_letters in states
                       if self.check_solution(known_clues, known_letters)]
            return results

        clue, evaluator, clue_letters, pattern_maker, constraints = self._solving_order[
            current_index]
        is_twin_value = states[0][0].get(clue, None)
        results = []
        for known_clues, known_letters in states:
            pattern = pattern_maker(known_clues)
            if current_index < self._max_debug_depth:
                print(f'{" | " * current_index} {clue.name} '
                      f'letters={clue_letters} pattern="{pattern.pattern}"')
            for next_letter_values in self.get_letter_values(known_letters, clue_letters):
                self._step_count += 1
                for letter, value in zip(clue_letters, next_letter_values):
                    known_letters[letter] = value
                clue_values = evaluator(known_letters)
                if is_twin_value:
                    twin_value = known_clues[clue]
                    if twin_value not in clue_values:
                        continue
                    if current_index <= self._max_debug_depth:
                        print(f'{" | " * current_index} {clue.name} TWIN {clue_letters} '
                              f'{next_letter_values} {twin_value} ({clue.length}): -->')
                    results.append(
                        (known_clues, twin_value, known_letters, next_letter_values))
                    continue
                for clue_value in clue_values:
                    if not (clue_value and pattern.fullmatch(clue_value)):
                        continue
                    known_clues.pop(clue, None)
                    if not self._allow_duplicates and clue_value in known_clues.values():
                        continue
                    known_clues[clue] = clue_value
                    bad_constraint = next((constraint for constraint in constraints if
                                           not constraint(known_clues)), None)
                    if bad_constraint:
                        if current_index <= self._max_debug_depth:
                            print(f'{" | " * current_index} '
                                  f'{clue.name} {"".join(clue_letters)} '
                                  f'{next_letter_values} {clue_value} '
                                  f'({clue.length}): --> X {bad_constraint.__name__}')
                        continue
                    if current_index <= self._max_debug_depth:
                        print(f'{" | " * current_index} {clue.name} '
                              f'{"".join(clue_letters)} '
                              f'{next_letter_values} {clue_value} ({clue.length}): -->')
                    results.append(
                        (known_clues, clue_value, known_letters, next_letter_values))
        return results


class Worker(multiprocessing.Process):
    solver: MultiEquationSolver

    def __init__(self, solver_type, task_queue, result_queue, *, id):
        super().__init__(name=f'[{id:02}]')
        self.solver_type = solver_type
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.id = id

        self._solving_order = None
        self.job = 0

    def run(self):
        if RUN_PROFILER:
            profiler = cProfile.Profile()
            profiler.enable()
        else:
            profiler = None

        solver = self.solver = self.solver_type()
        solver._debug = False
        solver._max_debug_depth = -1
        solver._step_count = 0
        self._solving_order = solver._solving_order = solver._get_solving_order()

        try:
            while True:
                try:
                    next_task = self.task_queue.get(False)
                except queue.Empty:
                    print(f"{self.name} is waiting for input")
                    next_task = self.task_queue.get()
                    print(f"{self.name} is no longer waiting for input")
                if next_task is None:  # Poison pill for shutdown
                    self.task_queue.task_done()
                    break
                self.job += 1
                self.worker_solve(next_task)
                self.task_queue.task_done()
        finally:
            self.task_queue.close()
            if profiler:
                profiler.disable()
                profiler.dump_stats(f'/tmp/solver-{self.id}.prof')

    def worker_solve(self, next_task):
        current_index, states = next_task
        assert states
        solver = self.solver
        task_queue = self.task_queue

        print(f'{self.name}#{self.job} READ ({current_index}, {len(states)}) '
              f'{self.task_queue}')

        local_queue = deque([(current_index, states)])

        queue_count = 0
        while local_queue:
            queue_count += 1
            write_count = 0
            write_total = 0

            current_index, states = local_queue.popleft()

            states = self.convert_state(current_index, states)
            solver_results = solver._inner_solve(current_index, states)
            if not solver_results:
                continue

            if current_index + 1 == len(self._solving_order):
                for clue_dict, _, letter_dict, _ in solver_results:
                    self.result_queue.put((clue_dict, letter_dict))
                print(f'{self.name}#{self.job}/{queue_count} solve {len(solver_results)}')
                continue

            task_queue_full = False
            if self.task_queue.is_get_waiting():
                max_queue_size, batch_size = 1, 10
            else:
                max_queue_size, batch_size = MAX_LOCAL_QUEUE_SIZE, 1000
            for batch in itertools.batched(solver_results, batch_size):
                if len(local_queue) >= max_queue_size and not task_queue_full:
                    try:
                        task_queue.put((current_index + 1, batch), False)
                        write_count += 1
                        write_total += len(batch)
                        continue  # move on to next batch
                    except queue.Full:
                        task_queue_full = True
                        pass  # fall through if the write fails
                local_queue.append((current_index + 1, batch))

            if write_count:
                print(f'{self.name}#{self.job}/{queue_count} WRITE '
                      f'({current_index}: {len(states):,}) -> '
                      f'({current_index + 1}: {write_total:,}) '
                      f'+{write_count} {self.task_queue}')

    def convert_state(self, current_index, states) -> Sequence[
            tuple[dict[Clue, ClueValue], dict[Letter, int]]]:
        if current_index == 0:
            states = [({}, {})]
        else:
            clue, _, clue_letters, _, _ = self._solving_order[current_index - 1]
            if clue_letters:
                states = [(clue_dict | {clue: value},
                           letter_dict | dict(zip(clue_letters, letter_values)))
                          for clue_dict, value, letter_dict, letter_values in states]
            else:
                states = [(clue_dict | {clue: value}, letter_dict)
                          for clue_dict, value, letter_dict, letter_values in states]
        return states
