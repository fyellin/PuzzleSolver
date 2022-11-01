from __future__ import annotations

from typing import Optional

import solver.ply.lex as lex
import solver.ply.yacc as yacc
from dataclasses import dataclass


class EquationParser:
    def __init__(self):
        # Build the lexer
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(module=self)

    tokens = ('NAME', 'NUMBER', 'POWER', 'SUBTRACT', 'MULTIPLY', 'FUNCTION')

    literals = ['+', '/', '(', ')', '=', ',', '!']

    # Tokens

    t_NAME = r'[a-zA-Z]'
    t_NUMBER = r'\d+'
    t_FUNCTION = r'"[^"]*"'
    t_POWER = r'\*\*|\^'
    t_ignore = "\n\t "
    t_SUBTRACT = r'-|−|–'    # -, \u2013 = n-dash, \u2212 = subtraction]
    t_MULTIPLY = r'\*|×'

    def t_error(self, t):
        raise SyntaxError(f"Illegal character {t.value[0]}")

    # Parsing rules
    def p_statement1(self, p):
        """statement : expr"""
        p[0] = [p[1]]

    def p_statement2(self, p):
        """statement : statement '=' expr"""
        p[1].append(p[3])
        p[0] = p[1]

    def p_expression(self, p):
        """expr : mult
           mult : just
           just : neg
           neg : expt
           expt : fact
           fact : atom
        """
        p[0] = p[1]

    def p_addition(self, p):
        """expr : expr '+' mult"""
        p[0] = Parse(operator='+', arg1=p[1], arg2=p[3])

    def p_subtraction(self, p):
        """expr : expr SUBTRACT mult"""
        p[0] = Parse(operator='-', arg1=p[1], arg2=p[3])

    def p_multiplication(self, p):
        """mult : mult MULTIPLY just"""
        p[0] = Parse(operator='*', arg1=p[1], arg2=p[3])

    def p_division(self, p):
        """mult : mult '/' just"""
        p[0] = Parse(operator='/', arg1=p[1], arg2=p[3])

    def p_juxtaposition(self, p):
        """just : just expt"""
        p[0] = Parse(operator='*', arg1=p[1], arg2=p[2])

    def p_negation(self, p):
        """neg : SUBTRACT neg"""
        p[0] = Parse(operator='-', arg1=p[2])

    def p_exponentiation(self, p):
        """expt :  fact POWER neg"""
        p[0] = Parse(operator='**', arg1=p[1], arg2=p[3])

    def p_factorial(self, p):
        """fact : fact '!'"""
        p[0] = Parse(operator='!', arg1=p[1])

    def p_parenthesis(self, p):
        """atom : '(' expr ')'"""
        p[0] = p[2]

    def p_number(self, p):
        """atom : NUMBER"""
        p[0] = Parse("const", arg1=p[1])

    def p_variable(self, p):
        """atom : NAME"""
        p[0] = Parse("var", arg1=p[1])

    def p_function_call(self, p):
        """atom : FUNCTION '(' csl ')' """
        p[0] = Parse('function', p[1][1:-1], p[3])

    def p_comma_separated_list_empty(self, p):
        """csl : """
        p[0] = []

    def p_comma_separated_list_one(self, p):
        """csl : expr """
        p[0] = [p[1]]

    def p_comma_separated_list_many(self, p):
        """csl : csl ',' expr """
        p[1].append(p[3])
        p[0] = p[1]

    def p_error(self, p):
        raise SyntaxError("Parsing failed")

    def parse(self, text):
        return self.parser.parse(text, lexer=self.lexer)


@dataclass
class Parse:
    operator: str
    arg1: Optional[Parse] | int | str
    arg2: Optional[Parse] = None

    def __str__(self):
        return self._to_string()

    def vars(self) -> set[str]:
        match self:
            case Parse('var', x, None):
                return {x}
            case Parse('const', _x, None):
                return set()
            case Parse('function', _name, args):
                return {x for arg in args for x in arg.vars()}
            case Parse(_, x, None):
                return x.vars()
            case Parse(_, x, y):
                return x.vars() | y.vars()
            case _:
                raise Exception

    def _to_string(self, functions: set[str] = frozenset(['fact'])):
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

        def internal(parse):
            match parse:
                case Parse('var', x, None) | Parse('const', x, None):
                    return str(x)
                case Parse('+', x, y):
                    return binop('add', '+', x, y)
                case Parse('*', x, y):
                    return binop('mul', '*', x, y)
                case Parse('-', x, y):
                    return unop('neg', '-', x) if y is None else binop('sub', '-', x, y)
                case Parse('/', x, y):
                    return binop('div', '/', x, y)
                case Parse('**', x, y):
                    return binop('pow', '**', x, y)
                case Parse('!', x, None):
                    return f'fact({internal(x)})'
                case Parse('function', name, args):
                    return name + '(' + ', '.join(internal(arg) for arg in args) + ')'
                case _:
                    raise Exception

        return internal(self)


if __name__ == '__main__':
    parser = EquationParser()
    temp = """
"sin"(x, y, z) + "cos"(z!) + "temp"()
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
        temp = parser.parse(string)[0]
        print(string, temp, temp.vars())
