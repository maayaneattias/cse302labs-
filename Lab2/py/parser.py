import ply.yacc as yacc
import bx_ast
import ast2tac
from lexer import lexer
from lexer import tokens

lvars = []


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


def p_expr_plus(p):
    """expr : expr PLUS expr"""
    # p[0]    p[1] p[2] p[3]
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'PLUS', [p[1], p[3]])


def p_expr_minus(p):
    """expr : expr MINUS expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'MINUS', [p[1], p[3]])


def p_expr_times(p):
    """expr : expr TIMES expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'TIMES', [p[1], p[3]])


def p_expr_div(p):
    """expr : expr DIV expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'DIV', [p[1], p[3]])


def p_expr_modulus(p):
    """expr : expr MODULUS expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'MODULUS', [p[1], p[3]])


def p_expr_bitand(p):
    """expr : expr BITAND expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BITAND', [p[1], p[3]])


def p_expr_bitor(p):
    """expr : expr BITOR expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BITOR', [p[1], p[3]])


def p_expr_bitxor(p):
    """expr : expr BITXOR expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BITXOR', [p[1], p[3]])


def p_expr_bitshl(p):
    """expr : expr BITSHL expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BITSHL', [p[1], p[3]])


def p_expr_bitshr(p):
    """expr : expr BITSHR expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BITSHR', [p[1], p[3]])


def p_expr_parens(p):
    """expr : LPAREN expr RPAREN"""
    p[0] = p[2]


def p_expr_uminus(p):
    """expr : MINUS expr %prec MODULUS"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], "UMINUS", [p[2]])


def p_expr_bitcompl(p):
    """expr : BITCOMPL expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], "BITCOMPL", [p[2]])


precedence = (("left", "BITOR"), ("left", "BITXOR"), ("left", "BITAND"),
              ("left", "BITSHR", "BITSHL"), ("left", "PLUS", "MINUS"),
              ("left", "TIMES", "DIV", "MODULUS"), ("right", "BITCOMPL"))


def p_program(p):
    """program : DEF MAIN LPAREN RPAREN LBRACE stmts RBRACE"""
    p[0] = p[6]


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
            | print"""
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


def p_error(p):
    if p == None:
        raise ValueError(
            "ERROR: Main function not defined/ not defined properly!")
    if not p: return
    raise ValueError(
        f'ERROR: (line: {p.lexer.lineno}) syntax error while processing {p.type}'
    )


parser = yacc.yacc(start="program")
