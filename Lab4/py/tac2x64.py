#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path

registers = ['%rdi', '%rsi', '%rdx', '%rcx', '%r8', '%r9']

binops = {'add':  'addq',
          'sub':  'subq',
          'mul':  (lambda ra, rb, rd: [f'\tmovq {ra}, %rax', f'\timulq {rb}', f'\tmovq %rax, {rd}']),
          'div':  (lambda ra, rb, rd: [f'\tmovq {ra}, %rax', f'\tcqto', f'\tidivq {rb}', f'\tmovq %rax, {rd}']),
          'mod':  (lambda ra, rb, rd: [f'\tmovq {ra}, %rax', f'\tcqto', f'\tidivq {rb}', f'\tmovq %rdx, {rd}']),
          'and':  'andq',
          'or':   'orq',
          'xor':  'xorq',
          'shl':  (lambda ra, rb, rd: [f'\tmovq {ra}, %r11', f'\tmovq {rb}, %rcx', f'\tsalq %cl, %r11', f'\tmovq %r11, {rd}']),
          'shr':  (lambda ra, rb, rd: [f'\tmovq {ra}, %r11', f'\tmovq {rb}, %rcx', f'\tsarq %cl, %r11', f'\tmovq %r11, {rd}'])
          }

unops = {'neg': 'negq', 'not': 'notq'}

jumps = ['jne', 'je', 'jl', 'jle', 'jg', 'jge',
         'jz', 'jnz', 'jnge', 'jng', 'jnle', 'jnl']


def stack_pos(var, temp_map, gvars, args, stack_size):
    if var not in temp_map:
        stack_size += 1
        temp_map[var] = f"{-8*stack_size}(%rbp)"
    return (temp_map, stack_size, temp_map[var])


def lookup_temp(var, temp_map, gvars, args, stack_size):
    if var in gvars:
        return (temp_map, stack_size, f"{var[1:]}(%rip)")
    elif var in args:
        if args.index(var) >= 6:
            return (temp_map, stack_size, f"{16+8*(args.index(var)-6)}(%rbp)")
    (temp_map, stack_size, dest) = stack_pos(
        var, temp_map, gvars, args, stack_size)
    return (temp_map, stack_size, dest)


def tac_to_asm(tac_instrs, gvars, name, proc_args, temp_map, stack_size):
    """
  Get the x64 instructions correspondign to the TAC instructions
  """
    asm = []
    for i in range(min(len(proc_args), 6)):
        temp_map, stack_size, result = lookup_temp(
            proc_args[i], temp_map, gvars, proc_args, stack_size)
        asm.append(f"\tmovq {registers[i]}, {result}")

    for instr in tac_instrs:
        opcode = instr['opcode']
        args = instr['args']
        dest = instr['result']

        if opcode == 'nop':
            pass

        elif opcode == 'const':
            assert len(args) == 1 and isinstance(args[0], int)
            temp_map, stack_size, result = lookup_temp(
                dest, temp_map, gvars, args, stack_size)
            asm.append(f'\tmovq ${args[0]}, {result}')

        elif opcode == 'copy':
            assert len(args) == 1
            temp_map, stack_size, arg = lookup_temp(
                args[0], temp_map, gvars, args, stack_size)
            temp_map, stack_size, result = lookup_temp(
                dest, temp_map, gvars, args, stack_size)
            asm.append(f'\tmovq {arg}, %r11')
            asm.append(f'\tmovq %r11, {result}')

        elif opcode in binops:
            assert len(args) == 2
            temp_map, stack_size, arg1 = lookup_temp(
                args[0], temp_map, gvars, args, stack_size)
            temp_map, stack_size, arg2 = lookup_temp(
                args[1], temp_map, gvars, args, stack_size)
            temp_map, stack_size, result = lookup_temp(
                dest, temp_map, gvars, args, stack_size)
            proc = binops[opcode]
            if isinstance(proc, str):
                asm.extend([
                    f'\tmovq {arg1}, %r11',
                    f'\t{proc} {arg2}, %r11',
                    f'\tmovq %r11, {result}'
                ])
            else:
                asm.extend(proc(arg1, arg2, result))

        elif opcode in unops:
            assert len(args) == 1
            temp_map, stack_size, arg = lookup_temp(
                args[0], temp_map, gvars, args, stack_size)
            temp_map, stack_size, result = lookup_temp(
                dest, temp_map, gvars, args, stack_size)
            proc = unops[opcode]
            asm.extend(
                [f'\tmovq {arg}, %r11', f'\t{proc} %r11', f'\tmovq %r11, {result}'])

        elif opcode in jumps:
            assert len(args) == 2
            assert dest == None
            temp_map, stack_size, args1 = lookup_temp(
                args[0], temp_map, gvars, args, stack_size)
            arg2 = args[1]
            asm.extend(
                [f'\tmovq {arg1}, %r11', f'\tcmpq $0, %r11', f'\t{opcode} {arg2}'])

        elif opcode in "jmp":
            assert len(args) == 1
            assert dest == None
            arg = args[0]
            asm.extend([f"\tjmp {arg}"])

        elif opcode in "label":
            assert len(args) == 1
            assert dest == None
            arg = args[0]
            asm.extend([arg + ":"])

        elif opcode == 'param':
            temp_map, stack_size, arg = lookup_temp(
                args[1], temp_map, gvars, args, stack_size)
            if args[0] <= 6:
                result = registers[args[0]-1]
                asm.append(f"\tmovq {arg}, {result}")
            else:
                asm.append(f"\tpushq {arg}")

        elif opcode == 'call':
            asm.append(f"\tcallq {args[0][1:]}")
            if result != '%_':
                temp_map, stack_size, result = lookup_temp(
                    dest, temp_map, gvars, args, stack_size)
                asm.append(f"\tmovq %rax, {result}")

        elif opcode == 'ret':
            if args == []:
                asm.extend(["\txorq %rax, %rax",
                           f"\tjmp .Lend_{name}"])
            else:
                temp_map, stack_size, arg = lookup_temp(
                    args[0], temp_map, gvars, args, stack_size)
                asm.extend([f"\tmovq {arg}, %rax",
                           f"\tjmp .Lend_{name}"])

        else:
            assert False, f'unknown opcode: {opcode}'

    stack_size = len(temp_map)
    if stack_size % 2 != 0:
        stack_size += 1
    asm = [f"\t.globl {name}", "\t.text", f"{name}:", "\tpushq %rbp",
           "\tmovq %rsp, %rbp", f"\tsubq ${8*stack_size}, %rsp"] + asm

    # Ensure main procedure returns nothing (%rax = 0)
    if name == 'main':
        asm.append("\txorq %rax, %rax")

    # Add exit assembly code
    asm += [f".Lend_{name}:", "\tmovq %rbp, %rsp",
            "\tpopq %rbp", "\tretq", "", ]

    return asm, temp_map, stack_size


def compile_tac(fname):
    rname = fname[:-9]
    tjs = None
    with open(fname, 'rb') as fp:
        tjs = json.load(fp)
    assert isinstance(tjs, list), tjs

    gvars = []
    asm = []
    stack = dict()
    stack_size = 0

    # Global Variables
    for decl in tjs:
        if 'var' in decl:
            name = decl['var']
            value = decl['init']
            gvars.append(name)
            asm.extend([f"\t.globl {name[1:]}",
                        "\t.data",
                        f"{name[1:]}: .quad {value}"])

    # Procedure Declarations
    for decl in tjs:
        if 'proc' in decl:
            name = decl['proc']
            args = decl['args']
            body = decl['body']
            proc_asm, stack, stack_size = tac_to_asm(
                body, gvars=gvars, name=name[1:], proc_args=args, temp_map=stack, stack_size=stack_size)
            asm.extend(proc_asm)

    xname = rname + '.exe'
    sname = rname + '.s'
    with open(sname, 'w') as afp:
        print(*asm, file=afp, sep='\n')
    print(f'{fname} -> {sname}')
    print(f'{sname} -> {xname}')
    return rname
