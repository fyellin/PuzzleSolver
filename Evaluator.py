import ast
import copy
import textwrap
from typing import NamedTuple, Callable, Dict, Optional, Sequence, Any

from ClueTypes import ClueValue, Letter

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

    @staticmethod
    def make(expression: str) -> 'Evaluator':
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


    @staticmethod
    def make2(expression: str) -> 'Evaluator':
        expression_ast: Any = ast.parse(expression.strip(), mode='eval')
        variables = sorted({Letter(node.id) for node in ast.walk(expression_ast) if isinstance(node, ast.Name)})

        module_def = copy.deepcopy(BASIC_MODULE_DEF)
        function_def = module_def.body[0]
        argument_name = function_def.args.args[0].arg
        # replace "left" with a tuple of the variables
        function_def.body[0].targets = [ast.Tuple(
            elts=[ast.Name(id=var, ctx=ast.Store()) for var in variables],
            ctx=ast.Store())]
        # replace "right" with a tuple of var_dict lookups, using the variable name as a string lookup key
        function_def.body[0].value = ast.Tuple(
            elts=[ast.Subscript(slice=ast.Index(value=ast.Str(var)),
                                value=ast.Name(id=argument_name, ctx=ast.Load()),
                                ctx=ast.Load())
                  for var in variables],
            ctx=ast.Load())
        # replace "expression" with the passed in expression.
        function_def.body[1].value = expression_ast.body

        ast.fix_missing_locations(module_def)
        code = compile(module_def, "", mode='exec')
        namespace: Dict[str, Any] = {}
        eval(code, None, namespace)
        return Evaluator(namespace['result'], variables)

    @staticmethod
    def make3(expression: str) -> 'Evaluator':
        expression_ast: Any = ast.parse(expression.strip(), mode='eval')
        variables = sorted({Letter(node.id) for node in ast.walk(expression_ast) if isinstance(node, ast.Name)})

        module_def = copy.deepcopy(BASIC_MODULE_DEF)
        function_def = module_def.body[0]
        argument_name = function_def.args.args[0].arg

        # noinspection PyPep8Naming
        # noinspection PyMethodMayBeStatic
        class ReWriter(ast.NodeTransformer):
            def visit_Name(self, node: ast.Name) -> Any:
                if node.id == "__LEFT__":
                    return ast.Tuple(
                        elts=[ast.Name(id=var, ctx=ast.Store()) for var in variables],
                        ctx=ast.Store())
                elif node.id == "__RIGHT__":
                    return ast.Tuple(
                        elts=[ast.Subscript(slice=ast.Index(value=ast.Str(var)),
                                            value=ast.Name(id=argument_name, ctx=ast.Load()),
                                            ctx=ast.Load())
                              for var in variables],
                        ctx=ast.Load())
                elif node.id == "__EXPRESSION__":
                    return expression_ast.body
                else:
                    return node

        module_def = ReWriter().visit(module_def)
        ast.fix_missing_locations(module_def)
        code = compile(module_def, "", mode='exec')
        namespace: Dict[str, Any] = {}
        eval(code, None, namespace)
        return Evaluator(namespace['result'], variables)

    def __call__(self, arg: Dict[Letter, int]) -> Optional[ClueValue]:
        return self.callable(arg)

    def __hash__(self) -> int:
        return id(self.callable)
