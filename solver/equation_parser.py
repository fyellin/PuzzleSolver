import ast
import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import batched
from typing import ClassVar
from pathlib import Path

USE_PREBUILT = True

# Note that "lark" is a module if USE_PREBUILT is True and a package if it is False.
# This makes "from XX import YY" difficult. However, qualified names, Lark.XX, work the
# same for both, so we use those.

if USE_PREBUILT:
    import solver.equation_parser_prebuilt as lark
else:
    import lark


GRAMMAR = r"""
%import common.WS
%import common.CNAME
%import common.LETTER
%import common.INT

statement : expr ("=" expr)*
expr      : term ((PLUS | MINUS) term)*               -> binary_op                                                                                           
term      : unary ((TIMES | DIVIDE) unary)*           -> binary_op                                                                                        
unary     : (PLUS | MINUS)* implicit                  -> prefix
implicit  : prefix+                                   -> implicit_multiply
prefix    : SQRT* power                               -> prefix
?power    : postfix POWER prefix                      -> binary_op
          | postfix
postfix   : atom (FACT | PRIME)*                      -> postfix
?atom     : variable
          | constant
          | "(" expr ")"
          | function_name "(" _arglist ")"            -> function_call
          | function_name "[" _arglist "]"            -> get_indexed
variable  : LETTER | "$" CNAME                        -> variable
constant  : INT                                       -> constant
function_name: "\"" CNAME "\""                       -> variable
          | "@" CNAME                                 -> variable
_arglist  : ( expr ("," expr)* )?

NUMBER: /\d+/
POWER: /\*\*|\^/
FACT: "!"
PRIME: "'"
PLUS: "+"
MINUS: /[-−–]/
TIMES: /[*×]/
DIVIDE: "/"
SQRT: "√"

%ignore WS
"""

@lark.v_args(inline=True)
class EquationTransformer(lark.Transformer):
    # Normalize token values that have multiple representations.
    def PLUS(self, _token):
        return '+'
    def MINUS(self, _token): return '-'
    def TIMES(self, _token): return '*'
    def DIVIDE(self, _token): return '/'
    def POWER(self, _token): return '**'
    def PRIME(self, _token): return '\''
    def FACT(self, _token): return '!'
    def SQRT(self, _token): return '√'

    # ------------------------------------------------------------------ rules

    def statement(self, *children):
        return [Parse(child) for child in children]

    def binary_op(self, first, *op_operand_pairs):
        # children: [value, op, value, op, value, ...]
        result = first
        for op, operand in batched(op_operand_pairs, 2, strict=True):
            result = op, result, operand
        return result

    def implicit_multiply(self, first, *more_operands):
        result = first
        for child in more_operands:
            result = ('*', result, child)
        return result

    def prefix(self, *children):
        # children: [op, op, ..., exponent_result]
        result = self.postfix(*children[::-1])
        return result

    def postfix(self, result, *operations):
        # children: [atom_result, op, op, ...]
        for op in operations:
            result = (op, result)
        return result

    def constant(self, name):
        return int(name.value)

    def variable(self, name):
        return name.value

    def function_call(self, name, *args):
        return 'function', name, args

    def get_indexed(self, name, *args):
        return 'getitem', name, tuple(args)


class EquationParser:
    _parser: ClassVar[lark.Lark | None] = None

    def __init__(self):
        if self._parser is None:
            type(self)._parser = self.get_parser(EquationTransformer())

    def parse(self, text: str) -> list[Parse]:
        try:
            return self._parser.parse(text)
        except lark.UnexpectedInput as e:
            print(f"Syntax error parsing {text}")
            raise SyntaxError(str(e)) from e

    @staticmethod
    def get_parser(transformer: lark.Transformer | None) -> lark.Lark:
        if not USE_PREBUILT:
            parser = lark.Lark(GRAMMAR, parser='lalr', cache=True, start='statement',
                               transformer=transformer)
        else:
            parser = lark.Lark_StandAlone(transformer=transformer)
            if lark.GRAMMAR_HASH != EquationParser.get_grammar_hash():
                raise Exception("Prebuilt parser is out of date")
        return parser

    @classmethod
    def generate_standalone(cls, filename: Path | str, compress=False, verbose=True):
        assert not USE_PREBUILT, "Cannot generate standalone parser from prebuilt parser"
        from lark.tools.standalone import gen_standalone
        with open(filename, "w") as out:
            parser = lark.Lark(GRAMMAR, parser='lalr', start='statement')
            gen_standalone(parser, out=out, compress=compress)
            out.write(f"\nGRAMMAR_HASH = '{cls.get_grammar_hash()}'\n")
        assert filename.exists() and filename.stat().st_size > 1_000, \
            f"Failed to generate {filename}"
        if verbose:
            print(f"Generated {filename} size: {filename.stat().st_size:,} bytes")

    @staticmethod
    def get_grammar_hash() -> str:
        return hashlib.sha256(GRAMMAR.encode('utf-8')).hexdigest()


@dataclass
class Parse:
    PARSE_BINOPS: ClassVar[dict[str, str]] = {
        '+': 'add', '-': 'sub', '*': 'mul', '/': 'div', '**': 'pow'
    }
    PARSE_UNOPS: ClassVar[dict[str, str]] = {
        '+': 'pos', '-': 'neg', '!': 'fact', '√': 'sqrt', '\'': 'prime'
    }

    BINARY_PRECEDENCE = {'+': 1, '-': 1, '*': 2, '/': 2, '**': 6}
    UNARY_PLUS_MINUS_PRECEDENCE = 3
    JUXTAPOSITION_PRECEDENCE = 4  # Not currently used
    UNARY_SQRT_PRECEDENCE = 5
    POSTFIX_PRECEDENCE = 7
    RIGHT_ASSOC = {'**'}

    expression: tuple

    def to_string(self, functions: set[str] = frozenset(), concise=False, pure=False
                  ) -> str:
        """
        :param functions:
            Operators to turn into function calls.  By default, includes fact, sqrt, prime
        :param concise:
            If true, remove unnecessary parentheses.  If false, include all parentheses
            except those around atoms and function calls.
        :param pure:
            If true, output fact, sqrt, and prime as !√' unless listed explicitly in
            the functions arg.
        :return:
        """
        if not pure:
            functions = functions | {'fact', 'sqrt', 'prime'}

        def _wrap(s, precedence, this_precedence):
            if concise:
                # If we bind less tightly than the outer function call, we need parens.
                need_parens = precedence > this_precedence
            else:
                # If we're calling this function, we need parentheses unless we're an
                # argument to a function call
                need_parens = precedence > 0
            return f'({s})' if need_parens else s

        def function_call(name: str, args, lparen='(', rparen=')') -> str:
            argument_list = ', '.join(inner(arg, 0) for arg in args)
            return f'{name}{lparen}{argument_list}{rparen}'

        def inner(expr, precedence) -> str:
            """Returns (string, precedence)."""
            match expr:
                # Atoms
                case str() as x:
                    return x
                case int() as x:
                    return str(x)

                # Function calls
                case ('function', name, args):
                    return function_call(name, args)
                case ('getitem', name, args):
                    return function_call(name, args, '[', ']')
                case (op, left, right) if self.PARSE_BINOPS[op] in functions:
                    return function_call(self.PARSE_BINOPS[op], [left, right])
                case (op, operand) if self.PARSE_UNOPS[op] in functions:
                    return function_call(self.PARSE_UNOPS[op], [operand])

                # Operators
                case (op, left, right) if op in self.BINARY_PRECEDENCE:
                    this_precedence = self.BINARY_PRECEDENCE[op]
                    left = inner(left, this_precedence + (.5 * (op in self.RIGHT_ASSOC)))
                    right = inner(right, this_precedence + (.5 * (op not in self.RIGHT_ASSOC)))
                    return _wrap(f'{left} {op} {right}', precedence, this_precedence)

                case ('!' | "'" as op, operand):  # postfix
                    this_precedence = self.POSTFIX_PRECEDENCE
                    argument = inner(operand, this_precedence)
                    return _wrap(f'{argument}{op}', precedence, this_precedence)

                case (op, operand):  # prefix (-, +, √)
                    this_precedence = (self.UNARY_SQRT_PRECEDENCE if op == '√' else
                                       self.UNARY_PLUS_MINUS_PRECEDENCE)
                    argument = inner(operand, this_precedence)
                    return _wrap(f'{op}{argument}', precedence, this_precedence)

                case _:
                    raise Exception(
                        f"Cannot handle '{expr}' when printing {self.expression!r}")

        return inner(self.expression, 0)

    def __str__(self) -> str:
        return self.to_string(concise=True)

    def vars(self) -> Sequence[str]:
        result = set()

        def internal(expression):
            match expression:
                case str() as x:
                    result.add(x)
                case int():
                    pass
                case ('function', _name, args) | ('getitem', _name, args):
                    for x in args:
                        internal(x)
                case (_, x):
                    internal(x)
                case (_, x, y):
                    internal(x)
                    internal(y)
                case _:
                    raise Exception(f"Cannot handle '{expression}'")
        internal(self.expression)
        return sorted(result)


if __name__ == '__main__':
    file = Path(__file__).parent / 'equation_parser_prebuilt.py'
    EquationParser.generate_standalone(file, compress=True)
