#!/usr/bin/env python3
"""
A class hierarchy for the AST of the BX language.
"""

####################
# Nodes


import enum


class Node:
    """Superclass of all AST nodes"""

    def __init__(self, sloc):
        """
    sloc -- source location (list of 6 numbers; see handout for meaning)
    """
        self.sloc = sloc


####################
# Types


class Type(enum.Enum):
    """Simple representation of the basic types of BX"""

    INT = enum.auto()
    BOOL = enum.auto()
    VOID = enum.auto()            # not needed at present

    def __str__(self):
        if self == Type.INT:
            return "int"
        if self == Type.BOOL:
            return "bool"
        if self == Type.VOID:
            return "void"
        raise ValueError


####################
# Expressions


class Expr(Node):
    """Superclass of all expressions"""

    def __init__(self, sloc):
        super().__init__(sloc)


class Variable(Expr):
    """Program variable"""

    def __init__(self, sloc, name: str):
        """
    name -- string representation of the name of the variable
    """
        super().__init__(sloc)
        self.name = name
        self.is_global = False

    def check_syntax(self, scopes, loop, in_proc):
        name = self.name
        declared = False
        # index not needed for now
        for i, scope in reversed(list(enumerate(scopes))):
            if name in scope:
                declared = True
                type = scope[name]
                break
        assert (declared == True
                ), f"ERROR [line: {self.sloc}]: Variable {name} not declared!"
        self.ty = type
        return type

    @property
    def js_obj(self):
        return {'tag': 'Variable',
                'name': self.name}


class Number(Expr):
    """Number literal"""

    # for now they are only ints (can be floats in the future)
    def __init__(self, sloc, value: int, ty=Type.INT):
        """
    value -- int representing the value of the number
    """
        super().__init__(sloc)
        self.value = value
        self.ty = ty

    def check_syntax(self, scopes, loop, in_proc):
        assert (self.value < 2**63 and self.value >= -(2**63)
                ), f"ERROR [line: {self.sloc}]: Value out of range (63 bits)!"
        return Type.INT

    @property
    def js_obj(self):
        return {'tag': 'Number',
                'value': str(self.value)}


class Boolean(Expr):
    """Boolean literal"""

    def __init__(self, sloc, value: bool):
        """
    value -- int representing the value of the boolean
    """
        super().__init__(sloc)
        if value == True:
            self.value = 1
        else:
            self.value = 0
        self.ty = Type.BOOL

    def check_syntax(self, scopes, loop, in_proc):
        return Type.BOOL

    @property
    def js_obj(self):
        return {'tag': 'Bool',
                'value': 1 if self.value else 0}


class OpApp(Expr):
    """Operator application"""

    def __init__(self, sloc, op: str, args):
        """
    op -- string representation of the operator
    args -- operands (all Expr instances)
    """
        super().__init__(sloc)
        assert isinstance(op, str), op
        self.op = op
        for arg in args:
            assert isinstance(arg, Expr), arg.__class__
        self.args = tuple(args)  # make container class explicitly a tuple

    def check_syntax(self, scopes, loop, in_proc):
        if len(self.args) == 2:
            type_l = self.args[0].check_syntax(scopes, loop, in_proc)
            type_r = self.args[1].check_syntax(scopes, loop, in_proc)
            assert (
                type_l == type_r
            ), f"ERROR [line: {self.sloc}]: Operation involving non-matching types: {type_l} and {type_r}!"
            bool_ops = ["BOOLAND", "BOOLOR"]
            if self.op in bool_ops:
                assert (
                    type_l == Type.BOOL
                ), f"ERROR [line: {self.sloc}]: Unsuppoprted type {type_l} for a boolean operation!"
        else:
            type_l = self.args[0].check_syntax(scopes, loop, in_proc)
            bool_ops = ["BOOLNOT"]
            if self.op in bool_ops:
                assert (
                    type_l == Type.BOOL
                ), f"ERROR [line: {self.sloc}]: Unsuppoprted type {type_l} for a boolean operation!"
            else:
                assert (
                    type_l == Type.INT
                ), f"ERROR [line: {self.sloc}]: Unsuppoprted type {type_l} for an integer operation!"
        bool_ret = [
            'LESS', 'LESSEQ', 'GREATER', 'GREATEREQ', 'BOOLEQ', 'BOOLNEQ',
            'BOOLNOT', 'BOOLAND', 'BOOLOR'
        ]
        if self.op in bool_ret:
            self.ty = Type.BOOL
            return Type.BOOL
        self.ty = Type.INT
        return Type.INT

    @property
    def js_obj(self):
        return {'tag': 'OpApp',
                'op': self.op,
                'args': [arg.js_obj for arg in self.args]}


class Call(Expr):
    """Procedural call"""

    def __init__(self, sloc, name: str, args):
        super().__init__(sloc)
        self.name = name
        self.args = args  # list of expr (potentially empty)

    def check_syntax(self, scopes, loop, in_proc):
        name = self.name
        if name == "print":
            assert (
                len(self.args) == 1
            ), f"ERROR [line: {self.sloc}]: Print functional call takes only one argument!"
            arg = self.args[0]
            arg.check_syntax(scopes, loop, in_proc)
            if arg.ty == Type.INT:
                self.name = "__bx_print_int"
            elif arg.ty == Type.BOOL:
                self.name = "__bx_print_bool"
            else:
                raise TypeError(
                    f'Cannot print() expressions of type: {arg.ty}')
            self.ty = Type.VOID
            return self.ty
        else:
            assert (
                name in scopes[0]
            ), f"ERROR [line: {self.sloc}]: Procedure {name} not defined!"
            func_arg_ty, func_ret_ty = scopes[0][name]
            assert (
                len(self.args) == len(func_arg_ty)
            ), f"ERROR [line: {self.sloc}]: Procedure {name} takes {len(func_arg_ty)} argument(s) - {len(self.args)} given!"
            #type = ([param.ty for param in decl.params], decl.ret_ty)
            for i in range(len(self.args)):
                arg = self.args[i]
                arg.check_syntax(scopes, loop, in_proc)
                assert (
                    arg.ty == func_arg_ty[i]
                ), f"ERROR [line: {self.sloc}]: Expected type of argument on position {i+1} is {func_arg_ty[i]} (actual arg type {arg.ty})!"
            self.ty = func_ret_ty
            return self.ty

    @property
    def js_obj(self):
        return {'tag': 'Call',
                'name': self.name,
                'args': [arg.js_obj for arg in self.args]}


####################
# Declarations


class Decl(Node):
    """Superclass of all declarations"""

    def __init__(self, sloc):
        super().__init__(sloc)


####################
# Statements


class Stmt(Node):
    """Superclass of all statements"""

    def __init__(self, sloc):
        super().__init__(sloc)
        self.has_return = False


class Vardecl(Stmt):
    """Vardeclaration"""

    def __init__(self, sloc, lhs: Variable, rhs: Expr, ty: Type, is_global: bool):
        """
    lhs -- a Variable instance
    rhs -- an Expr instance
    """
        self.ty = ty
        self.is_global = is_global
        if is_global == True:
            lhs.is_global = True
        super().__init__(sloc)
        self.lhs = lhs
        self.rhs = rhs

    def check_syntax(self, scopes, loop, in_proc):
        type = self.rhs.check_syntax(scopes, loop, in_proc)
        name = self.lhs.name
        assert (
            name not in scopes[-1]
        ), f"ERROR [line: {self.sloc}]: Variable {name} already declared in scope!"
        assert (
            type == self.ty), f"ERROR [line: {self.sloc}]: Type of variable {name} not matching with it's declaration!"
        scopes[-1][name] = type
        return type

    @property
    def js_obj(self):
        return {'tag': 'Vardecl',
                'lhs': self.lhs.js_obj,
                'rhs': self.rhs.js_obj}


class Assign(Stmt):
    """Assignments"""

    def __init__(self, sloc, lhs: Variable, rhs: Expr):
        """
    lhs -- a Variable instance
    rhs -- an Expr instance
    """
        super().__init__(sloc)
        self.lhs = lhs
        self.rhs = rhs

    def check_syntax(self, scopes, loop, in_proc):
        type_l = self.lhs.check_syntax(scopes, loop, in_proc)
        type_r = self.rhs.check_syntax(scopes, loop, in_proc)
        assert (
            type_l == type_r
        ), f"ERROR [line: {self.sloc}]: Expression of type {type_r} assinged to variable of type {type_l}!"
        return type_l

    @property
    def js_obj(self):
        return {'tag': 'Assign',
                'lhs': self.lhs.js_obj,
                'rhs': self.rhs.js_obj}


class Block(Stmt):
    def __init__(self, sloc, stmts):
        super().__init__(sloc)
        self.stmts = stmts
        self.sloc = sloc

    def check_syntax(self, scopes, loop, in_proc):
        scopes.append(dict())
        for stmt in self.stmts:
            stmt.check_syntax(scopes, loop, in_proc)
            if stmt.has_return:
                self.has_return = True
        return None

    @property
    def js_obj(self):
        return {'tag': 'Block',
                'stmts': [stmt.js_obj for stmt in self.stmts]}


class Ifelse(Stmt):
    def __init__(self, sloc, expr: Expr, blc: Block, ifrest):
        """
    expr -- an Expr instance
    blc -- a Block instance
    rest -- a Ifrest instance
    """
        super().__init__(sloc)
        assert isinstance(expr, Expr)
        assert isinstance(blc, Block)
        if ifrest:
            assert isinstance(ifrest, Block) or isinstance(ifrest, Ifelse)
        self.expr = expr
        self.blc = blc
        self.ifrest = ifrest

    def check_syntax(self, scopes, loop, in_proc):
        type_cond = self.expr.check_syntax(scopes, loop, in_proc)
        self.blc.check_syntax(scopes, loop, in_proc)
        if self.ifrest:
            self.ifrest.check_syntax(scopes, loop, in_proc)
        assert (
            type_cond == Type.BOOL
        ), f"ERROR [line: {self.sloc}]: Condition must be of type BOOL (current type: {type_cond})!"
        self.has_return = self.blc.has_return
        if self.ifrest:
            has_return_ifrest = self.ifrest.has_return
            if not has_return_ifrest:
                self.has_return = False
        return None

    @property
    def js_obj(self):
        return {'tag': 'IfElse',
                'condition': self.expr.js_obj,
                'block': self.blc.js_obj,
                'ifrest': self.ifrest.js_obj}


class While(Stmt):
    def __init__(self, sloc, expr: Expr, blc: Block):
        super().__init__(sloc)
        assert isinstance(expr, Expr)
        assert isinstance(blc, Block)
        self.expr = expr
        self.blc = blc

    def check_syntax(self, scopes, loop, in_proc):
        type_cond = self.expr.check_syntax(scopes, loop=True, in_proc=in_proc)
        self.blc.check_syntax(scopes, loop=True, in_proc=in_proc)
        assert (
            type_cond == Type.BOOL
        ), f"ERROR [line: {self.sloc}]: Condition must be of type BOOL (current type: {type_cond})!"
        return None

    @property
    def js_obj(self):
        return {'tag': 'While',
                'condition': self.expr.js_obj,
                'stmts': self.blc.js_obj}


class Break(Stmt):
    def __init__(self, sloc):
        super().__init__(sloc)

    def check_syntax(self, scopes, loop, in_proc):
        assert (loop == True
                ), f"ERROR [line: {self.sloc}]: Break used out of a loop!"
        return None

    @property
    def js_obj(self):
        return {'tag': 'Break'}


class Continue(Stmt):
    def __init__(self, sloc):
        super().__init__(sloc)

    def check_syntax(self, scopes, loop, in_proc):
        assert (loop == True
                ), f"ERROR [line: {self.sloc}]: Continue used out of a loop!"
        return None

    @property
    def js_obj(self):
        return {'tag': 'Continue'}


class Return(Stmt):
    def __init__(self, sloc, expr):
        super().__init__(sloc)
        self.expr = expr  # expr == None when we don't return a value
        self.has_return = True

    def check_syntax(self, scopes, loop, in_proc):
        if self.expr != None:
            self.expr.check_syntax(scopes, loop, in_proc)
            self.ty = self.expr.ty
        else:
            self.ty = Type.VOID
        assert (in_proc.ret_ty == self.ty
                ), f"ERROR [line: {self.sloc}]: Function {in_proc.name} should return {in_proc.ret_ty}, instead it returns {self.ty}!"
        return self.ty

    @property
    def js_obj(self):
        return {'tag': 'Return',
                'expr': self.expr.js_obj}


class Eval(Stmt):
    def __init__(self, sloc, expr: Expr):
        super().__init__(sloc)
        assert isinstance(expr, Expr)
        self.expr = expr

    def check_syntax(self, scopes, loop, in_proc):
        self.expr.check_syntax(scopes, loop, in_proc)
        self.ty = self.expr.ty
        return self.ty

    @property
    def js_obj(self):
        return {'tag': 'Eval',
                'expr': self.expr.js_obj}

####################
# Procedures


class Param(Node):
    """Parameters for procedure calls"""

    def __init__(self, sloc, name: str, ty: Type):
        super().__init__(sloc)
        self.name = name
        self.ty = ty

    def check_syntax(self, scopes, loop, in_proc):
        return self.ty

    @property
    def js_obj(self):
        return {'tag': 'Param',
                'name': self.name,
                'type': str(self.ty)}


class Procdecl(Decl):
    """Procedure declaration"""

    def __init__(self, sloc, name: str, params: list, ret_ty: Type, blc: Block):
        super().__init__(sloc)
        assert isinstance(blc, Block)
        assert all(isinstance(param, Param) for param in params)
        self.name = name
        self.params = params
        self.ret_ty = ret_ty
        self.blc = blc

    def check_syntax(self, scopes, loop, in_proc):
        scopes.append(dict())
        for param in self.params:
            scopes[-1][param.name] = param.ty
        self.blc.check_syntax(scopes, loop, in_proc)
        if self.blc.has_return == False and self.ret_ty != Type.VOID:
            raise ValueError(
                f"ERROR [line: {self.sloc}]: Procedure {self.name} is missing a return statement!")
        return self.ret_ty

    @property
    def js_obj(self):
        return {'tag': 'Procdecl',
                'name': self.name,
                'params': [param.js_obj for param in self.params],
                'ret_type': str(self.ret_ty),
                'block': self.blc.js_obj}


####################
# Programs


class Program(Node):
    def __init__(self, sloc, decls):
        super().__init__(sloc)
        self.decls = decls

    def check_syntax(self):
        scopes = [dict()]
        # First phase
        main_declare = False
        for decl in self.decls:
            if isinstance(decl, Vardecl):
                type = decl.ty
                name = decl.lhs.name
                assert (
                    name not in scopes[0]
                ), f"ERROR [line: {self.sloc}]: Variable {name} already declared in scope!"
                assert (isinstance(decl.rhs, Number) or isinstance(decl.rhs, Boolean)
                        ), f"ERROR [line: {self.sloc}]: Global variable {name} initialized with an expression different from Number or Boolean!"
                scopes[0][name] = type

            elif isinstance(decl, Procdecl):
                type = ([param.ty for param in decl.params], decl.ret_ty)
                name = decl.name
                assert (
                    name not in scopes[0]
                ), f"ERROR [line: {self.sloc}]: Procedure {name} already declared in scope!"
                if decl.name[:5] == "__bx_":
                    raise ValueError(
                        f"ERROR [line: {self.sloc}]: Procedure name can't start with '__bx_'!")
                if name == "main":
                    main_declare = True
                    assert (
                        decl.params == []
                    ), f"ERROR [line: {self.sloc}]: Procedure {name} should have no arguments!"
                    assert (
                        decl.ret_ty == Type.VOID
                    ), f"ERROR [line: {self.sloc}]: Procedure {name} should be of type void!"
                scopes[0][name] = type

            else:
                raise ValueError(
                    f"ERROR [line: {self.sloc}]: Only Variable and Procedure declarations are valid compilation units!")

        if main_declare == False:
            raise ValueError(
                f"ERROR [line: {self.sloc}]: Main procedure not declared!")

        # Second phase
        for decl in self.decls:
            # print("before_check: ", decl)
            if isinstance(decl, Procdecl):
                decl.check_syntax(scopes=scopes, loop=False, in_proc=decl)
            # print("after_check: ", decl)
