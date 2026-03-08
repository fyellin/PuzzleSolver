import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from enum import IntEnum
from itertools import batched
from pathlib import Path
from typing import ClassVar

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
function_name: "\"" CNAME "\""                        -> variable
          | "@" CNAME                                 -> variable
_arglist  : ( expr ("," expr)* )?

POWER: /\*\*|\^/
FACT: "!"
PRIME: "'"
PLUS: "+"
MINUS: /[-−–]/         # hyphen-minus, Unicode minus \u2212, en dash (\u2013) 
TIMES: /[*×]/          # asterisk, Unicode multiplication (\u00d7)

DIVIDE: "/"
SQRT: "√"

%ignore WS
"""


@lark.v_args(inline=True)
class EquationTransformer(lark.Transformer):
    # Normalize token values that have multiple representations.
    def MINUS(self, _token): return '-'
    def TIMES(self, _token): return '*'
    def POWER(self, _token): return '**'

    # ------------------------------------------------------------------ rules

    def statement(self, *children):
        return [Parse(child) for child in children]

    def binary_op(self, first, *op_operand_pairs):
        # children: [value, op, value, op, value, ...]
        result = first
        for op, operand in batched(op_operand_pairs, 2, strict=True):
            # op may be Token or string.
            result = str(op), result, operand
        return result

    def implicit_multiply(self, first, *more_operands):
        result = first
        for child in more_operands:
            result = '*', result, child
        return result

    def prefix(self, *children):
        # [op, op, ... atom_result]
        (*operations, result) = children
        for op in reversed(operations):
            result = str(op), result
        return result

    def postfix(self, result, *operations):
        # children: [atom_result, op, op, ...]
        for op in operations:
            result = str(op), result
        return result

    def constant(self, name):
        return int(name.value)

    def variable(self, name):
        return name.value

    def function_call(self, name, *args):
        return 'function', name, tuple(args)

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
            if EquationParser.get_grammar_hash() != lark.GRAMMAR_HASH:
                raise Exception("Prebuilt parser is out of date")
        return parser

    @classmethod
    def generate_standalone(cls, filename: Path | str, compress=False, verbose=True):
        import lark
        from lark.tools.standalone import gen_standalone
        with Path(filename).open("w") as out:
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

    class Precedence(IntEnum):
        NONE = 0
        ADD_SUB = 1
        MUL_DIV = 2
        POS_NEG = 3        # unary + and -
        IMPLICIT_MULTIPLY = 4
        SQRT = 5
        POWER = 6
        POSTFIX = 7        # ! and '

    BINARY_PRECEDENCE: ClassVar[dict[str, Precedence]] = {
        '+': Precedence.ADD_SUB, '-': Precedence.ADD_SUB,
        '*': Precedence.MUL_DIV, '/': Precedence.MUL_DIV,
        '**': Precedence.POWER,
    }
    RIGHT_ASSOC = frozenset({'**'})

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
            If true, output fact, sqrt, and prime as operators unless listed explicitly in
            the functions arg.
        :return:
        """
        if not pure:
            functions = functions | {'fact', 'sqrt', 'prime'}

        P = self.Precedence

        def _wrap(s, precedence, this_precedence):
            # In concise mode, we need to parenthesize ourselves if our precedence is
            # less tight (i.e. less than) the outside precedence.
            # In non-concise mode, we need to parenthesize ourselves until we are a
            # function argument
            need_parens = precedence > (this_precedence if concise else P.NONE)
            return f'({s})' if need_parens else s

        def function_call(name: str, args, lparen='(', rparen=')') -> str:
            argument_list = ', '.join(inner(arg, P.NONE) for arg in args)
            return f'{name}{lparen}{argument_list}{rparen}'

        def inner(expr, precedence) -> str:
            """Convert *expr* to a string, parenthesizing if needed.

            *precedence* is the binding strength of the enclosing operator.
            """
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

                # Operators
                case (op, left, right) if op in self.BINARY_PRECEDENCE:
                    if self.PARSE_BINOPS[op] in functions:
                        return function_call(self.PARSE_BINOPS[op], [left, right])
                    juxtaposition = pure and op == '*'
                    this_precedence = P.IMPLICIT_MULTIPLY if juxtaposition else self.BINARY_PRECEDENCE[op]
                    left = inner(left, this_precedence + (.5 * (op in self.RIGHT_ASSOC)))
                    right = inner(right, this_precedence + (.5 * (op not in self.RIGHT_ASSOC)))
                    argument = f'{left} {right}' if juxtaposition else f'{left} {op} {right}'
                    return _wrap(argument, precedence, this_precedence)

                case (op, operand) if self.PARSE_UNOPS[op] in functions:
                    return function_call(self.PARSE_UNOPS[op], [operand])

                case ('!' | "'" as op, operand):  # postfix
                    this_precedence = P.POSTFIX
                    argument = inner(operand, this_precedence)
                    return _wrap(f'{argument}{op}', precedence, this_precedence)

                case (op, operand):  # prefix (-, +, √)
                    this_precedence = (P.SQRT if op == '√' else
                                       P.POS_NEG)
                    argument = inner(operand, this_precedence)
                    return _wrap(f'{op}{argument}', precedence, this_precedence)

                case _:
                    raise Exception(
                        f"Cannot handle '{expr}' when printing {self.expression!r}")

        return inner(self.expression, P.NONE)

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
