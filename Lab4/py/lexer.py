import ply.lex as lex

reserved = {
    "int": "INT",
    "bool": "BOOL",
    "def": "DEF",
    "var": "VAR",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "break": "BREAK",
    "continue": "CONTINUE",
    "true": "TRUE",
    "false": "FALSE",
    "void": "VOID",
    "return": "RETURN"
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
    'COMMA',
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
t_BOOLAND = r"\&\&"
t_BOOLOR = r"\|\|"
t_BITAND = r"\&"
t_BITOR = r"\|"
t_BITXOR = r"\^"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_PLUS = r"\+"
t_MINUS = r"\-"
t_SEMICOLON = ";"
t_BITSHR = ">>"
t_BITSHL = "<<"
t_BITCOMPL = "~"
t_BOOLEQ = "=="
t_EQUAL = "="
t_COLON = ":"
t_COMMA = r','
t_LBRACE = "{"
t_RBRACE = "}"
t_LESSEQ = "<="
t_GREATEREQ = ">="
t_LESS = "<"
t_GREATER = ">"
t_BOOLNEQ = "!="
t_BOOLNOT = "!"


def t_IDENT(t):
    r"[A-Za-z_][A-Za-z0-9_]*"
    t.type = reserved.get(t.value, "IDENT")
    return t


def t_NUMBER(t):
    r"0|-?[1-9][0-9]*"
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
