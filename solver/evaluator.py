from __future__ import annotations

import ast
import textwrap
from typing import Any, Callable, Dict, NamedTuple, Optional, Sequence

from .clue_types import ClueValue, Letter


class Evaluator (NamedTuple):
    callable: Callable[[Dict[Letter, int]], Optional[ClueValue]]
    vars: Sequence[Letter]
    expression: str

    @classmethod
    def make(cls, expression: str, *,
             user_globals: Optional[Dict[str, Any]] = None) -> Evaluator:
        variables = cls._get_variables(expression)
        code = cls._get_code(expression, variables)
        compiled_code = cls._get_compiled_code(code, user_globals)
        return Evaluator(compiled_code, variables, expression)

    def with_alt_code_generator(self, code: str):
        variables = self.vars
        wrapped_code = f"""
            def result(value_dict):
                ({", ".join(variables)}) = ({", ".join(f'value_dict["{v}"]' for v in variables)})
                from solver import ClueValue
                try:
{textwrap.indent(textwrap.dedent(code), ' ' * 20)}
                except ArithmeticError:
                    return None
            """
        wrapped_code = textwrap.dedent(wrapped_code)
        compiled_code = self._get_compiled_code(wrapped_code, None)
        return self._replace(callable=compiled_code)

    @staticmethod
    def _get_variables(expression):
        expression_ast: Any = ast.parse(expression.strip(), mode='eval')
        variables = sorted({Letter(node.id) for node in ast.walk(expression_ast)
                            if isinstance(node, ast.Name) and len(node.id) == 1
                            })
        return variables

    @classmethod
    def _get_code(cls, expression, variables):
        importation = "import math" if 'math' in expression else ""

        code = f"""
        def result(value_dict):
            ({", ".join(variables)}) = ({", ".join(f'value_dict["{v}"]' for v in variables)})
            {importation}
            from solver import ClueValue
            try:
                value = {expression}
                int_value = int(value)
                return ClueValue(str(int_value)) if value == int_value > 0 else None
            except ArithmeticError:
                return None
        """
        return textwrap.dedent(code)

    @classmethod
    def _get_compiled_code(cls, code, user_globals: Optional[Dict[str, Any]]):
        my_globals = user_globals or globals()
        namespace: Dict[str, Any] = {}
        exec(code, my_globals, namespace)
        compiled_code = namespace['result']
        return compiled_code

    def __call__(self, arg: Dict[Letter, int]) -> Optional[ClueValue]:
        t = self.callable(arg)
        return t

    def __hash__(self) -> int:
        return id(self.callable)
