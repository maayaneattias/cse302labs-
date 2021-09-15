#classes for expression assignment: can be either a number, variable or an expression with operation


class Expr:
    pass

class Variable(Expr):
    def __init__(self, name, value, register):
        self.name = name
        self.value = value
        self.register = register

class Number(Expr):
    def __init__(self, number):
        self.number = number

class UnopApp(Expr):
    def __init__(self, op, arg):
        self.op = op
        self.arg = arg

class BinopApp(Expr):
    def __init__(self, arg1, op, arg2):
        self.arg1 = arg1
        self.op = op
        self.arg2 = arg2
