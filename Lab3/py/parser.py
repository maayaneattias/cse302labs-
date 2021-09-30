import ply.yacc as yacc
import bx_ast
import ast2tac
from lexer import lexer
from lexer import tokens

lvars = []

#Precedence Updated
precedence = (
            ("left", "BOOLOR"),("left", "BOOLAND"),
            ("left", "BITOR"), ("left", "BITXOR"), ("left", "BITAND"),
            ("nonassoc", "BOOLEQ", "BOOLNEQ"), ("nonassoc", "LESS", "LESSEQ", "GREATER", "GREATEREQ")
            ("left", "BITSHR", "BITSHL"), ("left", "PLUS", "MINUS"),
            ("left", "TIMES", "DIV", "MODULUS"), ("right", "BOOLNEQ", "UMINUS"),("right", "BITCOMPL"))


def p_expr_ident(p):
    """expr : IDENT"""
    if p[1] not in lvars:
        raise ValueError(
            "ERROR: (line: {}) Variable {} has not been declared!".format(
                p.lexer.lineno, p[1]))
    p[0] = bx_ast.Variable([p.lexer.lineno], p[1])


def p_var_ident(p):
    """var : IDENT"""
    p[0] = bx_ast.Variable([p.lexer.lineno], p[1])


def p_expr_number(p):
    """expr : NUMBER"""
    if int(p[1]) >= 2**63:
        raise ValueError(
            "ERROR: (line: {}) Value out of range (63 bits)!".format(
                p.lexer.lineno))
    p[0] = bx_ast.Number([p.lexer.lineno], int(p[1]))

def p_expr_parens(p):
    """expr : LPAREN expr RPAREN"""
    p[0] = p[2]

def p_expr_true(p):
    """expr : TRUE"""
    p[0] = bx_ast.Boolean([p.lexer.lineno], True)


def p_expr_false(p):
    """expr : FALSE"""
    p[0] = bx_ast.Boolean([p.lexer.lineno], False)


def p_expr_binop(p):
    '''expr : expr PLUS  expr
            | expr MINUS expr
            | expr TIMES  expr
            | expr DIV expr
            | expr MODULUS expr
            | expr BITAND expr
            | expr BITOR expr
            | expr BITXOR expr
            | expr BITSHL expr
            | expr BITSHR expr
            | expr LESS expr
            | expr LESSEQ expr
            | expr GREATER expr
            | expr GREATEREQ expr
            | expr BOOLEQ expr
            | expr BOOLNEQ expr
            | expr BOOLAND expr
            | expr BOOLOR expr'''
    p[0] = bx_ast.OpApp([p.lexer.lineno], p[2], [p[1], p[3]])

def p_expr_unop(p):
    '''expr : BITCOMPL expr
            | BOOLNOT expr'''
    p[0] = bx_ast.OpApp([p.lexer.lineno], p[1], [p[2]])

def p_expr_uminus(p):
    """expr : MINUS expr %prec MODULUS"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], "UMINUS", [p[2]])

    
def p_program(p):
    """program : DEF MAIN LPAREN RPAREN block"""
    p[0] = p[5]


def p_block(p):
    """block : LBRACE stmts RBRACE"""
    p[0] = p[2]


def p_stmts(p):
    """stmts :
             | stmts stmt"""
    if len(p) == 1:
        p[0] = []
    else:
        p[0] = p[1]
        p[0].append(p[2])


def p_stmt(p):
    """stmt :  vardecl
            | assign
            | print
            | ifelse
            | while
            | jump
            | block"""
    p[0] = p[1]


def p_stmt_assign(p):
    """assign : var EQUAL expr SEMICOLON"""
    if p[1].name not in lvars:
        raise ValueError("ERROR: (line: {}) Variable {} not declared!".format(
            p.lexer.lineno, p[1].name))
    p[0] = bx_ast.Assign([p.lexer.lineno], p[1], p[3], lvars)


def p_stmt_vardecl(p):
    """vardecl : VAR var EQUAL expr COLON INT SEMICOLON"""
    if p[2].name in lvars:
        raise ValueError(
            "ERROR: (line: {}) Variable {} already declared!".format(
                p.lexer.lineno, p[2].name))

    lvars.append(p[2].name)
    p[0] = bx_ast.Vardecl([p.lexer.lineno], p[2], p[4])


def p_stmt_print(p):
    """print : PRINT LPAREN expr RPAREN SEMICOLON"""
    p[0] = bx_ast.Print([p.lexer.lineno], p[3])


def p_stmt_ifelse(p):
    """ifelse: IF LPAREN expr RPAREN block ifrest"""
    p[0] = bx_ast.Ifelse([p.lexer.lineno], p[3],p[5],p[6])


def p_ifrest(p):
    """ifrest : 
                | ELSE ifelse 
                | ELSE block"""
    if len(p) == 1:
        p[0] = []
    else:
        p[0] = bx_ast.Ifrest([p.lexer.lineno], p[2])


def p_stmt_while(p):
    """while : WHILE LPAREN expr RPAREN block"""
    p[0] = bx_ast.While([p.lexer.lineno], p[3], p[5])


def p_continue(p):
    '''jump : CONTINUE SEMICOLON'''
    p[0] = bx_ast.Continue([p.lexer.lineno])
    
def p_break(p):
    '''jump : BREAK SEMICOLON'''
    p[0] = bx_ast.Break([p.lexer.lineno])

def p_error(p):
    if p == None:
        raise ValueError(
            "ERROR: Main function not defined/ not defined properly!")
    if not p: return
    raise ValueError(
        f'ERROR: (line: {p.lexer.lineno}) syntax error while processing {p.type}'
    )


parser = yacc.yacc(start="program")
