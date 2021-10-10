#!/usr/bin/env python3

import bx_ast as ast
from lexer import lexer
from parser import parser
import json
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


# alg (previous argument of prog) was deleted => update main function where we create an instance of Prog


class Prog:
    def __init__(self, ast_prog: ast.Program):
        self.localtemps = []
        self.instrs = []
        self.__tempmap = dict()
        self.__last = -1
        self.__last_label = -1
        # stack for Munching break and continue
        self._break_stack = []
        self._continue_stack = []
        for stmt in ast_prog.stmts:
            self.tmm_stmt(stmt)

    @property
    def js_obj(self):
        return [{'proc': '@main', 'body': [i.js_obj for i in self.instrs]}]

    def _fresh(self):
        self.__last += 1
        t = f'%{self.__last}'
        self.localtemps.append(t)
        return t

    def _fresh_label(self):
        self.__last_label += 1
        t = f'.L{self.__last_label}'
        return t

    def _lookup(self, var):
        t = self.__tempmap.get(var)
        if t is None:
            t = self._fresh()
            self.__tempmap[var] = t
        return t

    def _emit(self, opcode, args, result):
        self.instrs.append(Instr(opcode, args, result))

    def tmm_int_expr(self, expr, target):
        if isinstance(expr, ast.Variable):
            src = self._lookup(expr.name)
            self._emit('copy', [src], target)
        elif isinstance(expr, ast.Number):
            self._emit('const', [expr.value], target)
        elif isinstance(expr, ast.Boolean):
            self._emit('const', [expr.value], target)
        elif isinstance(expr, ast.OpApp):
            args = []
            for arg_expr in expr.args:
                arg_target = self._fresh()
                self.tmm_int_expr(arg_expr, arg_target)
                args.append(arg_target)
            self._emit(opcode_map[expr.op], args, target)
        else:
            raise ValueError(
                f'tmm_expr: [line:{expr.sloc}] unknown expr kind: {expr.__class__}')

    def tmm_bool_expr(self, bexpr, Lt, Lf):
        if isinstance(bexpr, ast.Boolean):
            if bexpr.value == True:
                self._emit('jmp', [Lt], None)
            else:
                self._emit('jmp', [Lf], None)

        elif isinstance(bexpr, ast.OpApp):
            if bexpr.op == 'BOOLNOT':
                self.tmm_bool_expr(bexpr.args[0], Lf, Lt)

            if bexpr.op == 'BOOLAND':
                Li = self._fresh_label()
                self.tmm_bool_expr(bexpr.args[0], Li, Lt)
                self._emit('label', [Li], None)
                self.tmm_bool_expr(bexpr.args[1], Li, Lt)

            if bexpr.op == 'BOOLOR':
                Li = self._fresh_label()
                self.tmm_bool_expr(bexpr.args[0], Lt, Li)
                self._emit('label', [Li], None)
                self.tmm_bool_expr(bexpr.args[1], Lt, Lf)

            if bexpr.op == 'BOOLEQ':
                t1 = self._fresh()
                t2 = self._fresh()
                self.tmm_int_expr(bexpr.args[0], t1)
                self.tmm_int_expr(bexpr.args[1], t2)
                self._emit('sub', [t1, t2], t1)
                self._emit('jz', [t1, Lt], None)
                self._emit('jmp', [Lf], None)

            if bexpr.op == 'BOOLNEQ':
                t1 = self._fresh()
                t2 = self._fresh()
                self.tmm_int_expr(bexpr.args[0], t1)
                self.tmm_int_expr(bexpr.args[1], t2)
                self._emit('sub', [t1, t2], t1)
                self._emit('jnz', [t1, Lt], None)
                self._emit('jmp', [Lf], None)

            if bexpr.op == 'LESS':
                t1 = self._fresh()
                t2 = self._fresh()
                self.tmm_int_expr(bexpr.args[0], t1)
                self.tmm_int_expr(bexpr.args[1], t2)
                self._emit('sub', [t1, t2], t1)
                self._emit('jl', [t1, Lt], None)
                self._emit('jmp', [Lf], None)

            if bexpr.op == 'LESSEQ':
                t1 = self._fresh()
                t2 = self._fresh()
                self.tmm_int_expr(bexpr.args[0], t1)
                self.tmm_int_expr(bexpr.args[1], t2)
                self._emit('sub', [t1, t2], t1)
                self._emit('jle', [t1, Lt], None)
                self._emit('jmp', [Lf], None)

            if bexpr.op == 'GREATER':
                t1 = self._fresh()
                t2 = self._fresh()
                self.tmm_int_expr(bexpr.args[0], t1)
                self.tmm_int_expr(bexpr.args[1], t2)
                self._emit('sub', [t1, t2], t1)
                self._emit('jg', [t1, Lt], None)
                self._emit('jmp', [Lf], None)

            if bexpr.op == 'GREATEREQ':
                t1 = self._fresh()
                t2 = self._fresh()
                self.tmm_int_expr(bexpr.args[0], t1)
                self.tmm_int_expr(bexpr.args[1], t2)
                self._emit('sub', [t1, t2], t1)
                self._emit('jge', [t1, Lt], None)
                self._emit('jmp', [Lf], None)
        else:
            raise ValueError(
                f'tmm_bool_expr: unknown stmt kind: {bexpr.__class__}')

    def tmm_stmt(self, stmt):
        if isinstance(stmt, ast.Assign):
            t_lhs = self._lookup(stmt.lhs.name)
            self.tmm_int_expr(stmt.rhs, t_lhs)
        elif isinstance(stmt, ast.Vardecl):
            t_lhs = self._lookup(stmt.lhs.name)
            self.tmm_int_expr(stmt.rhs, t_lhs)
        elif isinstance(stmt, ast.Print):
            t = self._fresh()
            self.tmm_int_expr(stmt.arg, t)
            self._emit('print', [t], None)
        elif isinstance(stmt, ast.Block):
            for stmt in stmt.stmts:
                self.tmm_stmt(stmt)
        elif isinstance(stmt, ast.Ifelse):
            Lt = self._fresh_label()
            Lf = self._fresh_label()
            Lo = self._fresh_label()
            self.tmm_bool_expr(stmt.expr, Lt, Lf)
            self._emit('label', [Lt], None)
            self.tmm_stmt(stmt.blc)
            self._emit('jmp', [Lo], None)
            self._emit('label', [Lf], None)
            # not an empty block, stmt to munch
            if isinstance(stmt.ifrest, ast.Block) and stmt.ifrest.stmts == []:
                pass
            else:
                self.tmm_stmt(stmt.ifrest)

            self._emit('label', [Lo], None)
        elif isinstance(stmt, ast.While):
            Lhead = self._fresh_label()
            Lbod = self._fresh_label()
            Lend = self._fresh_label()
            self._break_stack.append(Lend)
            self._continue_stack.append(Lhead)
            self._emit('label', [Lhead], None)
            self.tmm_bool_expr(stmt.expr, Lbod, Lend)
            self._emit('label', [Lbod], None)
            self.tmm_stmt(stmt.blc)
            self._emit('jmp', [Lhead], None)
            self._emit('label', [Lend], None)
            self._break_stack.pop()
            self._continue_stack.pop()
        elif isinstance(stmt, ast.Break):
            self._emit('jmp', [self._break_stack[-1]], None)
        elif isinstance(stmt, ast.Continue):
            self._emit('jmp', [self._continue_stack[-1]], None)
        else:
            raise ValueError(f'tmm_stmt: unknown stmt kind: {stmt.__class__}')


####################
# output json for tac for testing
def bx_to_tac_json(fname):
    assert fname.endswith('.bx')
    file = open(fname, "r")
    text = file.read()
    file.close()
    lexer.input(text)
    blc_stmts = parser.parse(lexer=lexer)
    stmts = blc_stmts.stmts.stmts
    # print(stmts[1].lhs)
    ast_prog = ast.Program([0], stmts)
    ast_prog.check_syntax()
    tac_prog = Prog(ast_prog)
    tacname = fname[:-2] + 'tac.json'
    with open(tacname, 'w') as fp:
        json.dump(tac_prog.js_obj, fp)
    print(f'{fname} -> {tacname}')
    return tacname
