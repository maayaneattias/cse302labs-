#!/usr/bin/env python3

"""
BX2 Syntax & Type Checker

Usage: ./bx2front.py file1.bx file2.bx ...
"""

import sys
import ast
from lexer import lexer
from parser import parser


def main():
    assert len(sys.argv) == 2
    fname = sys.argv[1]
    assert fname.endswith('.bx')
    file = open(fname, "r")
    text = file.read()
    file.close()
    lexer.input(text)
    ast_prog = parser.parse(lexer=lexer)
    ast_prog.check_syntax()


if __name__ == '__main__':
    main()
