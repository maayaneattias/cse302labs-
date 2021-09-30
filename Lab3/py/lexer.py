import ply.lex as lex

reserved = {
    "print": "PRINT",
    "int": "INT",
    "def": "DEF",
    "var": "VAR",
    "main": "MAIN",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "break": "BREAK",
    "contunue": "CONTUNUE",
    "true": "TRUE",
    "false": "FALSE"
}
tokens = (
    # punctuation
    'LPAREN',
    'RPAREN',
    'SEMICOLON',
    'EQUAL',
    'LBRACE',
    'RBRACE',
    'COLON',
    # arithmetic operators
    'PLUS',
    'MINUS',
    'TIMES',
    'DIV',
    'MODULUS',
    # bitewise operators
    'BITAND',
    'BITOR',
    'BITXOR',
    'BITSHL',
    'BITSHR',
    'BITCOMPL',
    # primitives
    'IDENT',
    'NUMBER',
    # boolean ops
    'LESS',
    'LESSEQ',
    'GREATER',
    'GREATEREQ',
    'BOOLEQ',
    'BOOLNEQ',
    'BOOLNOT',
    'BOOLAND',
    'BOOLOR') + tuple(reserved.values())

# ADD extra t for bools
t_TIMES = r"\*"
t_DIV = "/"
t_MODULUS = "%"
t_BITAND = r"\&"
t_BITOR = r"\|"
t_BITXOR = r"\^"
t_BITSHL = "<<"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_PLUS = r"\+"
t_MINUS = "-"
t_SEMICOLON = ";"
t_BITSHR = ">>"
t_BITCOMPL = "~"
t_EQUAL = "="
t_COLON = ":"
t_LBRACE = "{"
t_RBRACE = "}"

t_LESS = "<"
t_LESSEQ = "<="
t_GREATER = ">"
t_GREATEREQ = ">=" 
t_BOOLEQ = "==" 
t_BOOLNEQ = "!=" 
t_BOOLNOT = "!" 
t_BOOLAND = "&&" 
t_BOOLOR = "||" 


def t_IDENT(t):
    r"[A-Za-z_][A-Za-z0-9_]*"
    t.type = reserved.get(t.value, "IDENT")
    return t


def t_NUMBER(t):
    r"[0-9][0-9]*"
    t.value = int(t.value)
    return t


def t_error(t):
    print(f"Illegal character ’{t.value[0]}’ on line {t.lexer.lineno}")
    t.lexer.skip(1)


t_ignore = " \t\f\v"


def t_comment(t):
    r'//.*\n?'
    t.lexer.lineno += 1


def t_newline(t):
    r'\n'
    t.lexer.lineno += 1


lexer = lex.lex()