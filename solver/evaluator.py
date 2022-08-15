from __future__ import annotations

import math
import fractions
from collections.abc import Iterable, Sequence, Mapping
from typing import Any, Callable, NamedTuple, Optional
from .clue_types import ClueValue, Letter
from .equation_parser import EquationParser


class Evaluator (NamedTuple):
    wrapper: Callable[[Evaluator, dict[Letter, int]], Iterable[ClueValue]]
    callable: Callable[[dict[Letter, int]], Optional[ClueValue]]
    vars: Sequence[Letter]
    expression: str

    equation_parser = None

    @classmethod
    def from_string(cls, expression: str,
                    mapping: Optional[Mapping[str, Callable]] = None
                    ) -> Sequence[Evaluator]:
        if mapping is None:
            mapping = {}
        if cls.equation_parser is None:
            cls.equation_parser = EquationParser()
        parses = cls.equation_parser.parse(expression)
        my_globals = {'fact': math.factorial, 'math': math, **mapping}
        mapping_vars = set(mapping.keys())
        evaluators = []
        for parse in parses:
            variables = sorted(parse.vars())
            expression = parse.to_string(mapping_vars)
            code = f"lambda {', '.join(variables)}: {expression}"
            compiled_code = eval(code, my_globals, {})
            evaluators.append(
                Evaluator(cls.standard_wrapper, compiled_code, variables, expression))
        return evaluators

    @staticmethod
    def standard_wrapper(evaluator: Evaluator, value_dict: dict[Letter, int]
                         ) -> Iterable[ClueValue]:
        try:
            result = evaluator.callable(*(value_dict[x] for x in evaluator.vars))
            int_result = int(result)
            if result == int_result > 0:
                return ClueValue(str(int_result)),
            return ()
        except ArithmeticError:
            return ()

    def with_alt_wrapper(self, wrapper: Callable[[Evaluator, dict], Iterable[ClueValue]]
                         ) -> Evaluator:
        return self._replace(wrapper=wrapper)

    def globals(self):
        return self.callable.__globals__

    def __str__(self):
        return '<' + self.expression + '>'

    def __repr__(self):
        return str(self)

    def __call__(self, arg: dict[Letter, int]) -> Iterable[ClueValue]:
        return self.wrapper(self, arg)

    def __hash__(self) -> int:
        return id(self.callable)
