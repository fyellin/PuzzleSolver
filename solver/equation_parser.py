import solver.ply.lex as lex
import solver.ply.yacc as yacc


class EquationParser:
    def __init__(self):
        # Build the lexer
        self.lexer = lex.lex(module=self)
        self.parser = yacc.yacc(module=self)

    tokens = ('NAME', 'NUMBER', 'POWER', 'FACTORIAL', 'SUBTRACT', 'QUOTED')

    literals = ['+', '*', '/', '(', ')', '!', '=']

    # Tokens

    t_NAME = r'[a-zA-Z]'
    t_NUMBER = r'\d+'
    t_QUOTED = r'"[^"]*"'
    t_POWER = r'\*\*|\^'
    t_FACTORIAL = r'!'
    t_ignore = "\n\t "
    t_SUBTRACT = r'-|–|−'    # -, \u2013 = n-dash, \u2212 = subtraction

    def t_error(self, t):
        raise SyntaxError(f"Illegal character {t.value[0]}")

    # Parsing rules
    def p_statement1(self, p):
        """statement : expr"""
        p[0] = [p[1]]

    def p_statement2(self, p):
        """statement : statement '=' expr"""
        p[1].append(p[2])
        p[0] = p[1]

    def p_expression(self, p):
        """expr : mult
           mult : just
           just : neg
           neg : expt
           expt : fact
           fact : atom
           atom : NUMBER
           atom : NAME
        """
        p[0] = p[1]

    def p_addition(self, p):
        """expr : expr '+' mult"""
        p[0] = f'({p[1]} + {p[3]})'

    def p_subtraction(self, p):
        """expr : expr SUBTRACT mult"""
        p[0] = f'({p[1]} - {p[3]})'

    def p_multiplication(self, p):
        """mult : mult '*' just"""
        p[0] = f'({p[1]} * {p[3]})'

    def p_division(self, p):
        """mult : mult '/' just"""
        # p[0] = f'({p[1]} / {p[3]})'
        p[0] = f'div({p[1]}, {p[3]})'

    def p_juxtaposition(self, p):
        """just : just expt"""
        p[0] = f'({p[1]} * {p[2]})'

    def p_negation(self, p):
        """neg : SUBTRACT neg"""
        p[0] = f'(- {p[2]})'

    def p_exponentiation(self, p):
        """expt :  fact POWER neg"""
        p[0] = f'expt({p[1]}, {p[3]})'

    def p_factorial(self, p):
        """fact : fact FACTORIAL"""
        p[0] = f'fact({p[1]})'

    def p_parenthesis(self, p):
        """atom : '(' expr ')'"""
        p[0] = p[2]

    def p_quoted(self, p):
        """atom : QUOTED"""
        p[0] = p[1][1:-1]

    def p_error(self, p):
        raise SyntaxError("Parsing failed")

    def parse(self, text):
        return self.parser.parse(text, lexer=self.lexer)


if __name__ == '__main__':
    parser = EquationParser()
    temp = """
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
        print(string, parser.parse(string))
