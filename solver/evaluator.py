from __future__ import annotations

import ast
import math
import fractions
import operator
from collections.abc import Iterable, Sequence
from typing import Any, Callable, NamedTuple, Optional
from .clue_types import ClueValue, Letter


class Evaluator (NamedTuple):
    wrapper: Callable[[Evaluator, dict[Letter, int]], Iterable[ClueValue]]
    callable: Callable[[dict[Letter, int]], Optional[ClueValue]]
    vars: Sequence[Letter]
    expression: str

    @classmethod
    def make(cls, expression: str, *,
             user_globals: Optional[dict[str, Any]] = None) -> Evaluator:
        expression_ast = ast.parse(expression.strip(), mode='eval')
        variables = sorted({Letter(node.id) for node in ast.walk(expression_ast)
                            if isinstance(node, ast.Name) and len(node.id) == 1
                            })
        code = f"lambda {', '.join(variables)}: {expression}"
        my_globals = (user_globals or globals()).copy()
        my_globals.update((
            ('fact', math.factorial),
            ('div', fractions.Fraction),
            ('expt', operator.__pow__),
        ))
        namespace = {}
        compiled_code = eval(code, my_globals, namespace)
        return Evaluator(cls.standard_wrapper, compiled_code, variables, expression)

    @staticmethod
    def standard_wrapper(evaluator: Evaluator, value_dict: dict[Letter, int]) -> Iterable[ClueValue]:
        try:
            result = evaluator.callable(*(value_dict[x] for x in evaluator.vars))
            int_result = int(result)
            if result == int_result > 0:
                return ClueValue(str(int_result)),
            return ()
        except ArithmeticError:
            return ()

    def with_alt_wrapper(self, wrapper: Callable[[Evaluator, dict], Iterable[ClueValue]]) -> Evaluator:
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
