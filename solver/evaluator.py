import ast
import copy
import textwrap
from typing import NamedTuple, Callable, Dict, Optional, Sequence, Any

from .clue_types import ClueValue, Letter

BASIC_MODULE_DEF: Any = ast.parse(textwrap.dedent("""
def result(var_dict: Dict[Letter, int]) -> Optional[ClueValue]:
    __LEFT__ = __RIGHT__
    rvalue = __EXPRESSION__
    ivalue = int(rvalue)
    return ClueValue(str(ivalue)) if ivalue == rvalue > 0 else None
"""))


class Evaluator (NamedTuple):
    callable: Callable[[Dict[Letter, int]], Optional[ClueValue]]
    vars: Sequence[Letter]

    @classmethod
    def make(cls, expression: str) -> 'Evaluator':
        return cls.make1(expression)

    @classmethod
    def make1(cls, expression: str) -> 'Evaluator':
        expression_ast: Any = ast.parse(expression.strip(), mode='eval')
        variables = sorted({Letter(node.id) for node in ast.walk(expression_ast) if isinstance(node, ast.Name)})
        code = f"""
        def result(value_dict):
            ({", ".join(variables)}) = ({", ".join(f'value_dict["{v}"]' for v in variables)})
            rvalue = {expression}
            ivalue = int(rvalue)
            return ClueValue(str(ivalue)) if ivalue == rvalue > 0  else None
        """
        namespace: Dict[str, Any] = {}
        exec(textwrap.dedent(code), None, namespace)
        return Evaluator(namespace['result'], variables)

    @classmethod
    def make2(cls, expression: str) -> 'Evaluator':
        expression_ast: Any = ast.parse(expression.strip(), mode='eval')
        variables = sorted({Letter(node.id) for node in ast.walk(expression_ast) if isinstance(node, ast.Name)})

        module_def = copy.deepcopy(BASIC_MODULE_DEF)
        function_def = module_def.body[0]
        argument_name = function_def.args.args[0].arg

        # Change __LEFT__, __RIGHT__, and __EXPRESSION__ to their proper values
        id_map = {"__LEFT__":       cls.__assignment_left(variables),
                  "__RIGHT__":      cls.__assignment_right(variables, argument_name),
                  "__EXPRESSION__": expression_ast.body}

        # noinspection PyPep8Naming
        # noinspection PyMethodMayBeStatic
        class ReWriter(ast.NodeTransformer):
            def visit_Name(self, node: ast.Name) -> Any:
                return id_map.get(node.id, node)

        module_def = ReWriter().visit(module_def)

        # Convert the module_def into a callable function
        ast.fix_missing_locations(module_def)
        code = compile(module_def, "", mode='exec')
        namespace: Dict[str, Any] = {}
        eval(code, None, namespace)
        return Evaluator(namespace['result'], variables)

    @classmethod
    def __assignment_left(cls, variables: Sequence[Letter]) -> Any:
        return ast.Tuple(
            elts=[ast.Name(id=var, ctx=ast.Store()) for var in variables],
            ctx=ast.Store())

    @classmethod
    def __assignment_right(cls, variables: Sequence[Letter], argument_name: str) -> Any:
        return ast.Tuple(
            elts=[ast.Subscript(slice=ast.Index(value=ast.Str(var)),
                                value=ast.Name(id=argument_name, ctx=ast.Load()),
                                ctx=ast.Load())
                  for var in variables],
            ctx=ast.Load())

    def __call__(self, arg: Dict[Letter, int]) -> Optional[ClueValue]:
        return self.callable(arg)

    def __hash__(self) -> int:
        return id(self.callable)
