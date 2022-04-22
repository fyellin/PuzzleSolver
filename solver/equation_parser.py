from __future__ import annotations

from functools import reduce
from typing import NamedTuple, Optional

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
        return Parse(operator="**", arg1=p.postfix, arg2=p.prefix)

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
        return Parse(operator="const", arg1=p.NUMBER)

    @_('NAME')
    def atom(self, p):
        return Parse(operator="var", arg1=p.NAME)

    @_('FUNCTION "(" [ arglist ] ")"')
    def atom(self, p):
        return Parse(operator='function', arg1=p.FUNCTION, arg2=p.arglist or ())

    @_('expression { "," expression }')
    def arglist(self, p):
        return [p.expression0] + p.expression1

    def error(self, p):
        raise SyntaxError("Parsing failed")

    @staticmethod
    def __binop_builder(first, rest):
        def joiner(current, next):
            operator, argument = next
            return Parse(operator=operator, arg1=current, arg2=argument)
        return reduce(joiner, rest, first)

    @staticmethod
    def __unary_builder(first, rest):
        def joiner(previous, current):
            operator, = current
            return Parse(operator=operator, arg1=previous)
        return reduce(joiner, rest, first)


class EquationParser:
    def __init__(self):
        self.lexer = MyLexer()
        self.parser = MyParser()

    def parse(self, text):
        return self.parser.parse(self.lexer.tokenize(text))


class Parse(NamedTuple):
    operator: str
    arg1: Optional[Parse] | int | str
    arg2: Optional[Parse] = None

    def to_string(self, functions: set[str] = frozenset(['fact'])):
        def binop(func, operator, x, y):
            if func in functions:
                return f'{func}({internal(x)}, {internal(y)})'
            else:
                return f'({internal(x)} {operator} {internal(y)})'

        def unop(func, operator, x):
            if func in functions:
                return f'{func}({internal(x)})'
            else:
                return f'({operator} {internal(x)})'

        def postop(func, operator, x):
            if func in functions:
                return f'{func}({internal(x)})'
            else:
                return f'({internal(x)}{operator})'

        def internal(parse):
            match parse:
                case Parse('var', x, None) | Parse('const', x, None):
                    return str(x)
                case Parse('+', x, y):
                    return unop('pos', '+', x) if y is None else binop('add', '+', x, y)
                case Parse('-', x, y):
                    return unop('neg', '-', x) if y is None else binop('sub', '-', x, y)
                case Parse('*', x, y):
                    return binop('mul', '*', x, y)
                case Parse('/', x, y):
                    return binop('div', '/', x, y)
                case Parse('**', x, y):
                    return binop('pow', '**', x, y)
                case Parse('!', x, None):
                    return postop('fact', '!', x)
                case Parse('function', name, args):
                    return name + '(' + ', '.join(internal(arg) for arg in args) + ')'
                case _:
                    raise Exception

        return internal(self)

    def __str__(self):
        return self.to_string()

    def vars(self) -> set[str]:
        result = set()
        def internal(parse):
            match parse:
                case Parse('var', x, None):
                    result.add(x)
                case Parse('const', _x, None):
                    pass
                case Parse('function', _name, args):
                    for x in args:
                        internal(x)
                case Parse(_, x, None):
                    internal(x)
                case Parse(_, x, y):
                    internal(x); internal(y)
                case _:
                    raise Exception
        internal(self)
        return result


if __name__ == '__main__':
    from equation_parser_old import EquationParser as EquationParser2
    parser = EquationParser()
    parser2 = EquationParser2()
    temp = """
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
    for string in temp.strip().splitlines():
        print(string)
        for parse, parse2 in zip(parser.parse(string), parser2.parse(string)):
            print('    ', parse, parse.vars())
            assert str(parse) == str(parse2)
