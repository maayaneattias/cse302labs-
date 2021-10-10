#!/usr/bin/env python3
"""
A class hierarchy for the AST of the BX language.
"""

####################
# Nodes


class Node:
    """Superclass of all AST nodes"""

    def __init__(self, sloc):
        """
    sloc -- source location (list of 6 numbers; see handout for meaning)
    """
        self.sloc = sloc


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

    def check_syntax(self, scopes, loop):
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
        return type

    @property
    def js_obj(self):
        return {'tag': 'Variable',
                'name': self.name}


class Number(Expr):
    """Number literal"""

    def __init__(self, sloc, value: int):
        """
    value -- int representing the value of the number
    """
        super().__init__(sloc)
        self.value = value

    def check_syntax(self, scopes, loop):
        assert (self.value < 2**63
                ), f"ERROR [line: {self.sloc}]: Value out of range (63 bits)!"
        return "INT"

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

    def check_syntax(self, scopes, loop):
        return "BOOL"

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

    def check_syntax(self, scopes, loop):
        if len(self.args) == 2:
            type_l = self.args[0].check_syntax(scopes, loop)
            type_r = self.args[1].check_syntax(scopes, loop)
            assert (
                type_l == type_r
            ), f"ERROR [line: {self.sloc}]: Operation involving non-matching types: {type_l} and {type_r}!"
            bool_ops = ["BOOLAND", "BOOLOR"]
            if self.op in bool_ops:
                assert (
                    type_l == "BOOL"
                ), f"ERROR [line: {self.sloc}]: Unsuppoprted type {type_l} for a boolean operation!"
        else:
            type_l = self.args[0].check_syntax(scopes, loop)
            bool_ops = ["BOOLNOT"]
            if self.op in bool_ops:
                assert (
                    type_l == "BOOL"
                ), f"ERROR [line: {self.sloc}]: Unsuppoprted type {type_l} for a boolean operation!"
            else:
                assert (
                    type_l == "INT"
                ), f"ERROR [line: {self.sloc}]: Unsuppoprted type {type_l} for an integer operation!"
        bool_ret = [
            'LESS', 'LESSEQ', 'GREATER', 'GREATEREQ', 'BOOLEQ', 'BOOLNEQ',
            'BOOLNOT', 'BOOLAND', 'BOOLOR'
        ]
        if self.op in bool_ret:
            return "BOOL"
        return "INT"

    @property
    def js_obj(self):
        return {'tag': 'OpApp',
                'op': self.op,
                'args': [arg.js_obj for arg in self.args]}


####################
# Statements


class Stmt(Node):
    """Superclass of all statements"""

    def __init__(self, sloc):
        super().__init__(sloc)


class Vardecl(Stmt):
    """Vardeclaration"""

    def __init__(self, sloc, lhs: Variable, rhs: Expr):
        """
    lhs -- a Variable instance
    rhs -- an Expr instance
    """
        super().__init__(sloc)
        self.lhs = lhs
        self.rhs = rhs

    def check_syntax(self, scopes, loop):
        type = self.rhs.check_syntax(scopes, loop)
        name = self.lhs.name
        assert (
            name not in scopes[-1]
        ), f"ERROR [line: {self.sloc}]: Variable {name} already declared in scope!"
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

    def check_syntax(self, scopes, loop):
        type_l = self.lhs.check_syntax(scopes, loop)
        type_r = self.rhs.check_syntax(scopes, loop)
        assert (
            type_l == type_r
        ), f"ERROR [line: {self.sloc}]: Expression of type {type_r} assinged to variable of type {type_l}!"
        return type_l

    @property
    def js_obj(self):
        return {'tag': 'Assign',
                'lhs': self.lhs.js_obj,
                'rhs': self.rhs.js_obj}


class Print(Stmt):
    def __init__(self, sloc, arg: Expr):
        """
    arg -- an Expr instance
    """
        super().__init__(sloc)
        assert isinstance(arg, Expr)
        self.arg = arg

    def check_syntax(self, scopes, loop):
        type = self.arg.check_syntax(scopes, loop)
        assert (
            type == "INT"
        ), f"ERROR [line: {self.sloc}]: Print expression must be of type INT (current type {type})!"
        return type

    @property
    def js_obj(self):
        return {'tag': 'Print',
                'arg': self.arg.js_obj}


class Block(Stmt):
    def __init__(self, sloc, stmts):
        self.stmts = stmts
        self.sloc = sloc

    def check_syntax(self, scopes, loop):
        scopes.append(dict())
        for stmt in self.stmts:
            stmt.check_syntax(scopes, loop)
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

    def check_syntax(self, scopes, loop):
        type_cond = self.expr.check_syntax(scopes, loop)
        self.blc.check_syntax(scopes, loop)
        if self.ifrest:
            self.ifrest.check_syntax(scopes, loop)
        assert (
            type_cond == "BOOL"
        ), f"ERROR [line: {self.sloc}]: Condition must be of type BOOL (current type: {type_cond})!"
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

    def check_syntax(self, scopes, loop):
        type_cond = self.expr.check_syntax(scopes, loop=True)
        self.blc.check_syntax(scopes, loop=True)
        assert (
            type_cond == "BOOL"
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

    def check_syntax(self, scopes, loop):
        assert (loop == True
                ), f"ERROR [line: {self.sloc}]: Break used out of a loop!"
        return None


class Continue(Stmt):
    def __init__(self, sloc):
        super().__init__(sloc)

    def check_syntax(self, scopes, loop):
        assert (loop == True
                ), f"ERROR [line: {self.sloc}]: Continue used out of a loop!"
        return None


####################
# Programs


class Program(Node):
    def __init__(self, sloc, stmts):
        super().__init__(sloc)
        self.stmts = stmts

    def check_syntax(self):
        scopes = [dict()]
        for stmt in self.stmts:
            #print("before_check: ", stmt)
            stmt.check_syntax(scopes=scopes, loop=False)
            #print("after_check: ", stmt)
