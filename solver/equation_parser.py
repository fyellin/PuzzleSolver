from __future__ import annotations

import ast
from collections.abc import Sequence
from dataclasses import dataclass
from functools import reduce
from typing import ClassVar, cast

from solver.sly.lex import Lexer
from solver.sly.yacc import Parser


class MyLexer(Lexer):
    tokens = {'NAME', 'NUMBER', 'FUNCTION',
              'POWER', 'EXCLAMATION', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE'}
    ignore = " \t\n"
    literals = ['(', ')', '=', ',']

    # Tokens
    NAME = r'[a-zA-Z]'
    NUMBER = r'\d+'
    FUNCTION = r'"[^"]*"'
    POWER = r'\*\*|\^'   # must be defined before TIMES
    EXCLAMATION = r'!'
    PLUS = r'\+'
    MINUS = r'-|−|–'    # -, \u2013 = n-dash, \u2212 = subtraction]
    TIMES = r'\*|×'
    DIVIDE = r'/'

    def MINUS(self, t):
        t.value = '-'
        return t

    def TIMES(self, t):
        t.value = '*'
        return t

    def FUNCTION(self, t):
        t.value = t.value[1:-1]
        return t

    def error(self, t):
        raise SyntaxError(f"Illegal character {t.value[0]}")


class MyParser(Parser):
    debugfile = "/tmp/parser.out"
    tokens = MyLexer.tokens

    # statement
    @_('expression { "=" expression }')
    def statement(self, p):
        return [p.expression0] + p.expression1

    # expression
    @_('multiply { PLUS|MINUS multiply }')
    def expression(self, p):
        return self.__binop_builder(p[0], p[1])

    # multiply
    @_('juxtaposition { TIMES|DIVIDE juxtaposition }')
    def multiply(self, p):
        return self.__binop_builder(p[0], p[1])

    # juxtaposition
    @_('prefix { exponent }')  # It's not 'prefix { prefix }'.  Only first can have sign
    def juxtaposition(self, p):
        return self.__binop_builder(p[0], (('*', x) for x, in p[1]))

    # prefix
    @_('{ MINUS|PLUS } exponent')
    def prefix(self, p):
        return self.__unary_builder(p[1], p[0])

    # exponent
    @_('postfix')
    def exponent(self, p):
        return p.postfix

    @_('postfix POWER prefix')
    def exponent(self, p):
        return '**', p.postfix, p.prefix

    # postfix
    @_('atom { EXCLAMATION }')
    def postfix(self, p):
        return self.__unary_builder(p[0], p[1])

    # atom
    @_('"(" expression ")"')
    def atom(self, p):
        return p.expression

    @_('NUMBER')
    def atom(self, p):
        return 'const', p.NUMBER

    @_('NAME')
    def atom(self, p):
        return 'var', p.NAME

    @_('FUNCTION "(" [ arglist ] ")"')
    def atom(self, p):
        return 'function', p.FUNCTION, tuple(p.arglist or ())

    @_('expression { "," expression }')
    def arglist(self, p):
        return [p.expression0] + p.expression1

    def error(self, p):
        raise SyntaxError("Parsing failed")

    @staticmethod
    def __binop_builder(first, rest):
        def joiner(previous, current):
            operator, argument = current
            return operator, previous, argument
        return reduce(joiner, rest, first)

    @staticmethod
    def __unary_builder(first, rest):
        def joiner(previous, current):
            operator, = current
            return operator, previous
        return reduce(joiner, rest, first)


class EquationParser:
    def __init__(self) -> None:
        self.lexer = MyLexer()
        self.parser = MyParser()

    def parse(self, text: str) -> list[Parse]:
        return [Parse(x) for x in self.parser.parse(self.lexer.tokenize(text))]


@dataclass
class Parse:
    expression: tuple

    PARSE_BINOPS: ClassVar[dict[str, str]] = {'+': 'add', '-': 'sub', '*': 'mul',
                                              '/': 'div', '**': 'pow'}
    PARSE_UNOPS: ClassVar[dict[str], str] = {'+': 'pos', '-': 'neg', '!': 'fact'}

    def to_string(self, functions: set[str] = frozenset(['fact'])) -> str:
        def internal(expression):
            match expression:
                case ('var', x) | ('const', x):
                    return str(x)

                case ('function', name, args):
                    return name + '(' + ', '.join(internal(arg) for arg in args) + ')'

                case (binop, x, y):
                    func = self.PARSE_BINOPS[binop]
                    if func in functions:
                        return f'{func}({internal(x)}, {internal(y)})'
                    else:
                        return f'({internal(x)} {binop} {internal(y)})'

                case (unop, x):
                    func = self.PARSE_UNOPS[unop]
                    if func in functions:
                        return f'{func}({internal(x)})'
                    elif unop != '!':
                        return f'({unop} {internal(x)})'
                    else:
                        return f'({internal(x)} !)'

        return internal(self.expression)

    def __str__(self) -> str:
        return self.to_string()

    def vars(self) -> Sequence[str]:
        result = set()

        def internal(expression):
            match expression:
                case ('var', x):
                    result.add(x)
                case ('const', _x):
                    pass
                case ('function', _name, args):
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

    AST_BINOPS: ClassVar[dict[str, str]] = {'+': ast.Add, '-': ast.Sub, '*': ast.Mult,
                                            '/': ast.Div, '**': ast.Pow}
    AST_UNOPS: ClassVar[dict[str], str] = {'+': ast.UAdd, '-': ast.USub}

    def get_ast_expression(self, functions):
        def ast_function_call(name, args):
            return ast.Call(func=ast.Name(id=name, ctx=ast.Load()),
                            args=[ast_expression(x) for x in args],
                            keywords=[])

        def ast_expression(expression):
            match expression:
                case ('var', x):
                    return ast.Name(id=x, ctx=ast.Load())
                case ('const', x):
                    return ast.Constant(value=x)
                case ('function', name, args):
                    return ast_function_call(name, args)
                case (binop, x, y):
                    func = self.PARSE_BINOPS[binop]
                    if func in functions:
                        return ast_function_call(func, (x, y))
                    ast_op = self.AST_BINOPS[binop]
                    return ast.BinOp(
                        left=ast_expression(x), right=ast_expression(y), op=ast_op())
                case (unop, x):
                    func = self.PARSE_UNOPS[unop]
                    if func in functions or unop not in self.AST_UNOPS:
                        return ast_function_call(func, (x,))
                    ast_op = self.AST_UNOPS[unop]
                    return ast.UnaryOp(operand=ast_expression(x), op=ast_op())
                case _:
                    raise Exception(f"Cannot handle '{expression}'")

        variables = self.vars()
        result = ast.Expression(
                     body=ast.Lambda(args=ast.arguments(
                              args=[ast.arg(arg=var) for var in variables],
                              posonlyargs=[], kwonlyargs=[], kw_defaults=[], defaults=[],
                          ),
                          body=ast_expression(self.expression)))
        return ast.fix_missing_locations(result)


ITEM_STRING = """
"sin"(x, y, z) = "cos"(---z!!!) = "temp"()
ARABLE
PLOU/(G/H)
O(V – U)M 
(M + A)PLE
Q+U+I+D
J(E+E)–R
JELLY–P(E+A+R)
(S+H)^(O+O) +T
E+(X+E)RCISE+S
A+(NX+I+ET)Y
MI(X – E)D
–(V–I)^C(T+O)+(R+Y)!
(Y+E)LL+V^(I+O+L)
(D + R)^(UG)(AB)^(B(R + E) – V)
(W–R)^Y +(N+E+C)/K
"""

ITEMS = ITEM_STRING.strip().splitlines()


def run():
    from equation_parser_old import EquationParser as EquationParser2
    parser = EquationParser()
    parser2 = EquationParser2()
    for string in ITEMS:
        print(string)
        for parse, parse2 in zip(parser.parse(string), parser2.parse(string)):
            print('    ', parse, parse.vars())
            assert str(parse) == str(parse2)


def run2():
    parser = EquationParser()
    for string in ITEMS:
        parse = parser.parse(string)
        for equation in parse:
            print(string)
            expression = equation.get_ast_expression({'fact'})
            print(ast.unparse(expression.body))
            compile(cast(ast, expression), filename='', mode='eval')


if __name__ == '__main__':
    run2()
