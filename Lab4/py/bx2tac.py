#!/usr/bin/env python3

import json
from bx_ast import Type
from parser import parser
from lexer import lexer
import bx_ast as ast

# Prog became Proc and was adapted
# check if we need to add things in opcode_map
# in the munching add a condition for call -> add a Call class in AST ;
# AST needs to be adapted

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

    def __repr__(self):
        return f"{{opcode: {self.opcode}, args: {self.args}, result: {self.result}}}"

####################
# Global Variables


class GlobalVar:

    def __init__(self, var, init):
        self.var = var
        self.init = init

    @property
    def js_obj(self):
        return {
            'var': self.var,
            'init': self.init
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

# class Prog:
#     def __init__(self, ast_prog: ast.Program):


class Proc:
    def __init__(self, ast_proc: ast.Procdecl, gvars):
        self.name = '@'+ast_proc.name
        self.args = ['%'+ast_proc.params[i].name for i in range(
            len(ast_proc.params))]

        self.instrs = []

        self.localtemps = []

        self.__last = -1
        self.__last_label = -1

        # Global Variable Scope
        self.scope_stack = [{gvar.var[1:]: gvar.var for gvar in gvars}]

        # Procedure Arguments Scope
        self.scope_stack.append({arg[1:]: arg for arg in self.args})

        # stack for Munching break and continue
        self._break_stack = []
        self._continue_stack = []

        for stmt in ast_proc.blc.stmts:
            self.tmm_stmt(stmt)

    @property
    def js_obj(self):
        return {'proc': self.name, 'args': self.args, 'body': [i.js_obj for i in self.instrs]}

    def _fresh(self):
        self.__last += 1
        t = f'%{self.__last}'
        self.localtemps.append(t)
        return t

    def _fresh_label(self):
        self.__last_label += 1
        t = f'.L{self.__last_label}'
        return t

    def _lookup(self, var, scope=-1):
        t = self.scope_stack[scope].get(var)
        if t is None:
            if scope == -len(self.scope_stack):
                t = self._fresh()
                self.scope_stack[-1][var] = t
            else:
                t = self._lookup(var, scope-1)
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
            if expr.op == '!':
                Lt = self._fresh_label()
                Lf = self._fresh_label()
                Lo = self._fresh_label()
                self.tmm_bool_expr(expr, Lt, Lf)
                self._emit('label', [Lt], None)
                t_res = self._fresh()
                self.tmm_int_expr(ast.Boolean([], True), t_res)
                self._emit('copy', [t_res], target)
                self._emit('jmp', [Lo], None)
                self._emit('label', [Lf], None)
                self.tmm_int_expr(ast.Boolean([], False), t_res)
                self._emit('copy', [t_res], target)
                self._emit('label', [Lo], None)
            else:
                args = []
                for arg_expr in expr.args:
                    arg_target = self._fresh()
                    self.tmm_int_expr(arg_expr, arg_target)
                    args.append(arg_target)
                self._emit(opcode_map[expr.op], args, target)

        elif isinstance(expr, ast.Call):
            n_args = len(expr.args)
            for i in range(min(6, n_args)):
                arg_target = self._fresh()
                self.tmm_int_expr(expr.args[i], arg_target)
                self._emit('param', [i+1, arg_target], None)
            for i in range(n_args-1, 5, -1):
                arg_target = self._fresh()
                self.tmm_int_expr(expr.args[i], arg_target)
                self._emit('param', [i+1, arg_target], None)
            self._emit('call', ['@'+expr.name, n_args], target)

        else:
            raise ValueError(
                f'tmm_expr: [line:{expr.sloc}] unknown expr kind: {expr.__class__}')

    def tmm_bool_expr(self, bexpr, Lt, Lf):
        if isinstance(bexpr, ast.Boolean):
            if bexpr.value == True:
                self._emit('jmp', [Lt], None)
            else:
                self._emit('jmp', [Lf], None)

        if isinstance(bexpr, ast.Number):
            if bexpr.value:
                self._emit('jmp', [Lt], None)
            else:
                self._emit('jmp', [Lf], None)

        if isinstance(bexpr, ast.Variable):
            t_dest = self.fresh_tmp()
            self.tmm_int_expr(bexpr, t_dest)
            self._emit('jz', [t_dest, Lf], None)
            self._emit('jnz', [t_dest, Lt], None)

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
                self._emit('jnle', [t1, Lt], None)
                self._emit('jmp', [Lf], None)
            if bexpr.op == 'GREATEREQ':
                t1 = self._fresh()
                t2 = self._fresh()
                self.tmm_int_expr(bexpr.args[0], t1)
                self.tmm_int_expr(bexpr.args[1], t2)
                self._emit('sub', [t1, t2], t1)
                self._emit('jnl', [t1, Lt], None)
                self._emit('jmp', [Lf], None)

        else:
            raise ValueError(
                f'tmm_bool_expr: unknown stmt kind: {bexpr.__class__}')

    def tmm_stmt(self, stmt):
        if isinstance(stmt, ast.Vardecl):
            t_lhs = self._lookup(stmt.lhs.name)
            self.tmm_int_expr(stmt.rhs, t_lhs)

        elif isinstance(stmt, ast.Block):
            self.scope_stack.append(dict())
            for stmt in stmt.stmts:
                self.tmm_stmt(stmt)
            self.scope_stack.pop()

        elif isinstance(stmt, ast.Assign):
            t_lhs = self._lookup(stmt.lhs.name)
            self.tmm_int_expr(stmt.rhs, t_lhs)

        elif isinstance(stmt, ast.Eval):
            self.tmm_int_expr(stmt.expr, None)

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

        elif isinstance(stmt, ast.Return):
            if stmt.expr:
                t_lhs = self._fresh()
                self.tmm_int_expr(stmt.expr, t_lhs)
                self._emit('ret', [t_lhs], None)
            else:
                self._emit('ret', ['%_'], None)

        else:
            raise ValueError(f'tmm_stmt: unknown stmt kind: {stmt.__class__}')


####################
# output json for tac for testing
def bx_to_tac_json(fname):
    assert fname.endswith('.bx')
    gvars = []
    procs = []

    file = open(fname, "r")
    text = file.read()
    file.close()
    lexer.input(text)
    ast_prog = parser.parse(lexer=lexer)
    ast_prog.check_syntax()

    def add_gvar(decl):
        name = '@'+decl.lhs.name
        value = decl.rhs.value
        gvar = GlobalVar(name, value)
        gvars.append(gvar)

    # Global Variables
    for decl in ast_prog.decls:
        if isinstance(decl, ast.Vardecl):
            add_gvar(decl)
            # transform into json

    # Function Declarations
    for decl in ast_prog.decls:
        if isinstance(decl, ast.Procdecl):
            proc_tac = Proc(decl, gvars)
            # convert tac into json
            procs.append(proc_tac)

    full = gvars + procs
    full_json = []
    for elem in full:
        full_json.append(elem.js_obj)

    tacname = fname[:-2] + 'tac.json'
    with open(tacname, 'w') as fp:
        json.dump(full_json, fp)
    print(f'{fname} -> {tacname}')
    return tacname


# bx_to_tac_json("../examples/fizzbuzz.bx")
