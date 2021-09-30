#!/usr/bin/env python3

import bx_ast as ast

####################
# Instructions


class Instr:
    # reduce memory pressure by eliding the dynamic dictionary
    __slots__ = ['opcode', 'args', 'result']

    def __init__(self, opcode, args, result):
        self.opcode = opcode
        self.args = args
        self.result = result

    @property
    def js_obj(self):
        return {
            'opcode': self.opcode,
            'args': self.args,
            'result': self.result
        }


####################
# Procedures

opcode_map = {
    'PLUS': 'add',
    'MINUS': 'sub',
    'TIMES': 'mul',
    'DIV': 'div',
    'MODULUS': 'mod',
    'BITAND': 'and',
    'BITOR': 'or',
    'BITXOR': 'xor',
    'BITSHL': 'shl',
    'BITSHR': 'shr',
    'BITCOMPL': 'not',
    'UMINUS': 'neg'
}


class Prog:
    def __init__(self, ast_prog: ast.Program, alg):
        self.localtemps = []
        self.instrs = []
        self.__tempmap = dict()
        self.__last = -1
        #for v in ast_prog.lvars:
        #  self._emit('const', [0], self._lookup(v))
        if alg == 'tmm':
            for stmt in ast_prog.stmts:
                self.tmm_stmt(stmt)
        else:
            for stmt in ast_prog.stmts:
                self.bmm_stmt(stmt)

    @property
    def js_obj(self):
        return [{'proc': '@main', 'body': [i.js_obj for i in self.instrs]}]

    def _fresh(self):
        self.__last += 1
        t = f'%{self.__last}'
        self.localtemps.append(t)
        return t

    def _lookup(self, var):
        t = self.__tempmap.get(var)
        if t is None:
            t = self._fresh()
            self.__tempmap[var] = t
        return t

    def _emit(self, opcode, args, result):
        self.instrs.append(Instr(opcode, args, result))

    def tmm_expr(self, expr, target):
        if isinstance(expr, ast.Variable):
            src = self._lookup(expr.name)
            self._emit('copy', [src], target)
        elif isinstance(expr, ast.Number):
            self._emit('const', [expr.value], target)
        elif isinstance(expr, ast.OpApp):
            args = []
            for arg_expr in expr.args:
                arg_target = self._fresh()
                self.tmm_expr(arg_expr, arg_target)
                args.append(arg_target)
            self._emit(opcode_map[expr.op], args, target)
        else:
            raise ValueError(f'tmm_expr: unknown expr kind: {expr.__class__}')

    def bmm_expr(self, expr):
        if isinstance(expr, ast.Variable):
            return self._lookup(expr.name)
        elif isinstance(expr, ast.Number):
            target = self._fresh()
            self._emit('const', [expr.value], target)
            return target
        elif isinstance(expr, ast.OpApp):
            args = [self.bmm_expr(arg) for arg in expr.args]
            target = self._fresh()
            self._emit(opcode_map[expr.op], args, target)
            return target
        else:
            raise ValueError(f'bmm_expr: unknown expr kind: {expr.__class__}')

    def tmm_stmt(self, stmt):
        if isinstance(stmt, ast.Assign):
            t_lhs = self._lookup(stmt.lhs.name)
            self.tmm_expr(stmt.rhs, t_lhs)
        elif isinstance(stmt, ast.Vardecl):
            t_lhs = self._lookup(stmt.lhs.name)
            self.tmm_expr(stmt.rhs, t_lhs)
        elif isinstance(stmt, ast.Print):
            t = self._fresh()
            self.tmm_expr(stmt.arg, t)
            self._emit('print', [t], None)
        else:
            raise ValueError(f'tmm_stmt: unknown stmt kind: {stmt.__class__}')

    def bmm_stmt(self, stmt):
        if isinstance(stmt, ast.Assign):
            t_lhs = self._lookup(stmt.lhs.name)
            t_rhs = self.bmm_expr(stmt.rhs)
            self._emit('copy', [t_rhs], t_lhs)
        elif isinstance(stmt, ast.Vardecl):
            t_lhs = self._lookup(stmt.lhs.name)
            t_rhs = self.bmm_expr(stmt.rhs)
            self._emit('copy', [t_rhs], t_lhs)
        elif isinstance(stmt, ast.Print):
            t = self.bmm_expr(stmt.arg)
            self._emit('print', [t], None)
        else:
            raise ValueError(f'bmm_stmt: unknown stmt kind: {stmt.__class__}')


####################
# Driver

import tac2asm
import json


def ast_to_tac_json(fname, alg):
    assert fname.endswith('.json')
    with open(fname, 'rb') as fp:
        js_obj = json.load(fp)
        ast_prog = ast.Program.load(js_obj['ast'])
    tac_prog = Prog(ast_prog, alg)
    tacname = fname[:-4] + 'tac.json'
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
    tacname = ast_to_tac_json(opts.fname[0], alg)
    if opts.keepgoing: tac2asm.compile_tac(tacname)
