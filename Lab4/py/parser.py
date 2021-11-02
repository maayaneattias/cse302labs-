import ply.yacc as yacc
import bx_ast
from lexer import lexer
from lexer import tokens

precedence = (("left", "BOOLOR"), ("left", "BOOLAND"), ("left", "BITOR"),
              ("left", "BITXOR"), ("left", "BITAND"), ("nonassoc", "BOOLEQ",
                                                       "BOOLNEQ"),
              ("nonassoc", "LESS", "LESSEQ", "GREATER", "GREATEREQ"), ("left",
                                                                       "BITSHR",
                                                                       "BITSHL"),
              ("left", "PLUS", "MINUS"), ("left", "TIMES", "DIV", "MODULUS"),
              ("right", "BOOLNOT"), ("right", "BITCOMPL"))


def p_expr_ident(p):
    """expr : IDENT"""
    p[0] = bx_ast.Variable([p.lexer.lineno], p[1])


def p_var_ident(p):
    """var : IDENT"""
    p[0] = bx_ast.Variable([p.lexer.lineno], p[1])


def p_expr_number(p):
    """expr : NUMBER"""
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


def p_expr_less(p):
    """expr : expr LESS expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'LESS', [p[1], p[3]])


def p_expr_lesseq(p):
    """expr : expr LESSEQ expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'LESSEQ', [p[1], p[3]])


def p_expr_greater(p):
    """expr : expr GREATER expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'GREATER', [p[1], p[3]])


def p_expr_greatereq(p):
    """expr : expr GREATEREQ expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'GREATEREQ', [p[1], p[3]])


def p_expr_booleq(p):
    """expr : expr BOOLEQ expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BOOLEQ', [p[1], p[3]])


def p_expr_boolneq(p):
    """expr : expr BOOLNEQ expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BOOLNEQ', [p[1], p[3]])


def p_expr_booland(p):
    """expr : expr BOOLAND expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BOOLAND', [p[1], p[3]])


def p_expr_boolor(p):
    """expr : expr BOOLOR expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BOOLOR', [p[1], p[3]])


def p_expr_boolnot(p):
    """expr : BOOLNOT expr"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], 'BOOLNOT', [p[2]])


def p_expr_bitcompl(p):
    '''expr : BITCOMPL expr'''
    p[0] = bx_ast.OpApp([p.lexer.lineno], "BITCOMPL", [p[2]])


def p_expr_uminus(p):
    """expr : MINUS expr %prec MODULUS"""
    p[0] = bx_ast.OpApp([p.lexer.lineno], "UMINUS", [p[2]])


def p_program(p):
    """program : DEF MAIN LPAREN RPAREN block"""
    p[0] = bx_ast.Block([p.lexer.lineno], p[5])


def p_block(p):
    """block : LBRACE stmts RBRACE"""
    p[0] = bx_ast.Block([p.lexer.lineno], p[2])


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
    p[0] = bx_ast.Assign([p.lexer.lineno], p[1], p[3])


def p_stmt_vardecl(p):
    """vardecl : VAR var EQUAL expr COLON INT SEMICOLON"""
    p[0] = bx_ast.Vardecl([p.lexer.lineno], p[2], p[4])


def p_stmt_print(p):
    """print : PRINT LPAREN expr RPAREN SEMICOLON"""
    p[0] = bx_ast.Print([p.lexer.lineno], p[3])


def p_stmt_ifelse(p):
    """ifelse : IF LPAREN expr RPAREN block ifrest"""
    p[0] = bx_ast.Ifelse([p.lexer.lineno], p[3], p[5], p[6])


def p_ifrest(p):
    """ifrest : 
              | ELSE ifelse 
              | ELSE block"""
    if len(p) == 1:
        p[0] = bx_ast.Block([p.lexer.lineno], [])
    else:
        p[0] = p[2]


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
    if not p:
        return
    raise ValueError(
        f'ERROR: (line: {p.lexer.lineno}) syntax error while processing {p.type}'
    )


parser = yacc.yacc(start="program")
