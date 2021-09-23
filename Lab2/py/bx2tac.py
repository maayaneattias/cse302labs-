from lexer import lexer
from parser import parser
import bx_ast as ast
import tac2asm
import ast2tac

import json
import sys

file_in = sys.argv[1]


def bx_to_tac_json(fname, alg):
    assert fname.endswith('.bx')
    file = open(fname, "r")
    text = file.read()
    file.close()
    lexer.input(text)
    stmts = parser.parse(lexer=lexer)
    ast_prog = ast.Program([0], [], stmts)
    tac_prog = ast2tac.Prog(ast_prog, alg)
    tacname = fname[:-2] + 'tac.json'
    with open(tacname, 'w') as fp:
        json.dump(tac_prog.js_obj, fp)
    print(f'{fname} -> {tacname}')
    return tacname


if __name__ == '__main__':
    import sys, argparse
    ap = argparse.ArgumentParser(description='Codegen: AST(JSON) to TAC(JSON)')
    ap.add_argument(
        '--bmm',
        dest='bmm',
        action='store_true',
        default=False,
        help='Do bottom-up maximal munch (incompatible with --tmm)')
    ap.add_argument('--tmm',
                    dest='tmm',
                    action='store_true',
                    default=False,
                    help='Do top-down maximal munch (incompatible with --bmm)')
    ap.add_argument('--continue',
                    dest='keepgoing',
                    action='store_true',
                    default=False,
                    help='Continue with later stages of the compilation chain')
    ap.add_argument('fname',
                    metavar='FILE',
                    type=str,
                    nargs=1,
                    help='The AST(JSON) file to process')
    opts = ap.parse_args(sys.argv[1:])
    if opts.tmm and opts.bmm:
        raise ValueError('Cannot use both --tmm and --bmm')
    alg = 'tmm' if opts.tmm or not opts.bmm else 'bmm'
    tacname = bx_to_tac_json(opts.fname[0], alg)
    if opts.keepgoing: tac2asm.compile_tac(tacname)
