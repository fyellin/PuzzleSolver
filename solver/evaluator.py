from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence, Callable
from dataclasses import dataclass
from typing import ClassVar, cast

from .clue_types import ClueValue, Letter
from .equation_parser import EquationParser

WrapperType = Callable[['Evaluator', dict[Letter, int]], Iterable[ClueValue]]


@dataclass
class Evaluator:
    _wrapper: WrapperType
    _compiled_code: Callable[[dict[Letter, int]], ClueValue | None]
    _expression: str
    _vars: Sequence[Letter]
    _equation_parser: ClassVar[EquationParser] = None

    @classmethod
    def create_evaluator(cls, expression: str,
                         mapping: Mapping[str, Callable] | None = None,
                         wrapper: Callable[[Evaluator, dict], Iterable[ClueValue]] | None = None,
                         ) -> Evaluator:
        result, = cls.create_evaluators(expression, mapping, wrapper)
        return result

    @classmethod
    def create_evaluators(cls, expression: str,
                          mapping: Mapping[str, Callable] | None = None,
                          wrapper: Callable[[Evaluator, dict], Iterable[ClueValue]] | None = None,
                          ) -> Sequence[Evaluator]:
        if cls._equation_parser is None:
            cls._equation_parser = EquationParser()
        if mapping is None:
            mapping = {}
        wrapper = wrapper or cls.standard_wrapper

        parses = cls._equation_parser.parse(expression)
        my_globals = {'fact': cls.factorial, 'sqrt': cls.sqrt, 'math': math, **mapping}
        mapping_vars = set(mapping.keys())
        evaluators = []
        for parse in parses:
            variables = cast(Sequence[Letter], sorted(parse.vars()))
            expression = parse.to_string(mapping_vars, False)
            code = f"lambda {', '.join(variables)}: {expression}"
            compiled_code = eval(code, my_globals, {})
            evaluators.append(Evaluator(wrapper, compiled_code, expression, variables))
        return evaluators

    @staticmethod
    def factorial(i):
        if (j := int(i)) == i and j >= 0:
            return math.factorial(j)
        raise ArithmeticError

    @staticmethod
    def sqrt(i):
        if i >= 0:
            result = math.isqrt(i)
            if result * result == i:
                return result
        raise ArithmeticError

    @property
    def vars(self) -> Sequence[Letter]:
        return self._vars

    @property
    def compiled_code(self):
        return self._compiled_code

    def standard_wrapper(self, value_dict: dict[Letter, int]) -> Iterable[ClueValue]:
        try:
            result = self._compiled_code(*(value_dict[x] for x in self._vars))
            int_result = int(result)
            if result == int_result > 0:
                return ClueValue(str(int_result)),
            return ()
        except ArithmeticError:
            return ()

    def raw_call(self, value_dict: dict[Letter, int]) -> Iterable[int]:
        return self._compiled_code(*(value_dict[x] for x in self._vars))

    def set_wrapper(self, wrapper: WrapperType):
        self._wrapper = wrapper

    def __str__(self):
        return '<' + self._expression + '>'

    def __repr__(self):
        return str(self)

    def __call__(self, arg: dict[Letter, int]) -> Iterable[ClueValue]:
        return self._wrapper(self, arg)

    __hash__ = object.__hash__

    __eq__ = object.__eq__
