#!/usr/bin/python3
"""
Copyright (C) 2022 NyanCatTW1
This file is part of stage0-subleq.

stage0-subleq is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

stage0-subleq is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with stage0-subleq.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys
from inspect import currentframe

# Let lsq_to_hex worry about these instructions instead
lsq_insts = ["var", "label", "addr",
             "abssq", "relsq", "lblsq",
             "subaddr", "zeroaddr",
             "raw", "rem"]
consts = []


# Converts a from hex string to int if it's not already int type
def ensureInt(a):
    if not isinstance(a, int):
        return int(a, 16)
    return a


# Records a constant for post processing
def recordConst(a):
    a = ensureInt(a)
    if a not in consts:
        consts.append(a)
    return f"CONST_{a:X}"


def getInstName(frame):
    ret = frame.f_code.co_name
    if ret == "inst_set":
        ret = "set"
    return ret


def printArgs(args):
    args = [f"{x:x}" if type(x) == int else x for x in args]
    return " ".join(args)


def logSimple():
    frame = currentframe().f_back
    if frame.f_locals["v"] > 0:
        print(f"rem {getInstName(frame)} {printArgs(frame.f_locals['args'])}")


def logStart():
    frame = currentframe().f_back
    if frame.f_locals["v"] > 0:
        print()
        print(f"rem Start {getInstName(frame)} {printArgs(frame.f_locals['args'])}")


def logEnd():
    frame = currentframe().f_back
    if frame.f_locals["v"] > 0:
        print(f"rem End {getInstName(frame)}")
        print()


# Subtracts a by b
def sub(args, v=0):
    a, b = args
    logSimple()
    print(f"relsq {a} {b} 1")


# Sets a to 0
def zero(args, v=0):
    assert len(args) == 1
    a = args[0]
    logSimple()
    sub([a, a], v - 1)


# Decreases a by val (Constant)
def dec(args, v=0):
    a, val = args
    val = ensureInt(val)
    logSimple()
    print(f"relsq {a} {recordConst(val)} 1")


# Decreases a by val (Constant), and jumps to lbl if a <= 0 after operation
def decleq(args, v=0):
    a, val, lbl = args
    val = ensureInt(val)
    logSimple()
    print(f"lblsq {a} {recordConst(val)} {lbl}")


# Increases a by val (Constant)
def inc(args, v=0):
    a, val = args
    val = ensureInt(val)
    logSimple()
    dec([a, -val], v - 1)


# Increases a by val (Constant), and jumps to lbl if a <= 0 after operation
def incleq(args, v=0):
    a, val, lbl = args
    val = ensureInt(val)
    logSimple()
    decleq([a, -val, lbl], v - 1)


# Sets a to val (Constant)
def inst_set(args, v=1):
    a, val = args
    val = ensureInt(val)
    logSimple()
    zero([a], v - 1)
    inc([a, val], v - 1)


# Relatively jumps by a instructions
def reljmp(args, v=0):
    assert len(args) == 1
    a = args[0]
    logSimple()
    print(f"relsq ZERO ZERO {a}")


# Jumps to a label
def lbljmp(args, v=0):
    assert len(args) == 1
    lbl = args[0]
    logSimple()
    print(f"lblsq ZERO ZERO {lbl}")


# Sets a to -b
def movneg(args, v=1):
    a, b = args
    logSimple()
    zero([a], v - 1)
    sub([a, b], v - 1)


# Sets a to b, using tmp as a temporary storage
def mov(args, v=2):
    a, b, tmp = args
    logStart()
    movneg([tmp, b], v - 1)
    movneg([a, tmp], v - 1)
    logEnd()


# Fetches a character from SERIAL_IN into a, using tmp as a temporary storage
def getchar(args, v=2):
    a, tmp = args
    logStart()
    inst_set([tmp, 1], v - 1)
    print(f"relsq {tmp} SERIAL_IN 2")
    reljmp([-1], v - 1)
    zero(["SERIAL_IN"], v - 1)
    movneg([a, tmp], v - 1)
    logEnd()


# Outputs a character into SERIAL_IN, using tmp as a temporary storage
def putchar(args, v=2):
    a, tmp = args
    logStart()
    print("relsq SERIAL_OUT ZERO 2")
    reljmp([-1], v - 1)
    movneg([tmp, a], v - 1)
    dec([tmp, 1], v - 1)
    movneg(["SERIAL_OUT", tmp], v - 1)
    logEnd()


# Decreases all references of a symbol by b
def decaddr(args, v=0):
    sym, b = args
    logSimple()
    print(f"subaddr {sym} {recordConst(b)}")


# Sets a to val in one operation, instead of setting it to 0 first
def set_safe(args, v=2):
    a, val, tmp, tmp2 = args
    val = ensureInt(val)
    logStart()
    mov([tmp, a, tmp2], v - 1)
    dec([tmp, val], v - 1)
    sub([a, tmp], v - 1)
    logEnd()


# Jumps to dst's address if a < b
def jl(args, v=2):
    a, b, dst, tmp, tmp2 = args
    logStart()
    mov([tmp, a, tmp2], v - 1)
    # Don't jump if a == b
    inc([tmp, 1], v - 1)
    print(f"lblsq {tmp} {b} {dst}")
    logEnd()


# Multiplies a by 16
def mul_16(args, v=1):
    a, tmp = args
    logStart()
    zero([tmp], v - 1)
    for _i in range(5):
        sub([tmp, a], v - 1)
    for _i in range(3):
        sub([a, tmp], v - 1)
    logEnd()


# Multiplies a by 256
def mul_256(args, v=1):
    a, tmp = args
    logStart()
    mul_16([a, tmp], v - 1)
    mul_16([a, tmp], v - 1)
    logEnd()


# Does a = -a
def neg(args, v=1):
    a, tmp, tmp2 = args
    logStart()
    movneg([tmp, a], v - 1)
    mov([a, tmp, tmp2], v - 1)
    logEnd()


# Sets the address of sym to the value of val
def setaddr(args, v=2):
    sym, val, tmp = args
    logStart()
    print(f"zeroaddr {sym}")
    movneg([tmp, val], v - 1)
    print(f"subaddr {sym} {tmp}")
    logEnd()


# Does a += b
def add(args, v=2):
    a, b, tmp = args
    logStart()
    movneg([tmp, b], v - 1)
    sub([a, tmp], v - 1)
    logEnd()


# Does a *= 8
def mul_8(args, v=1):
    a, tmp = args
    logStart()
    movneg([tmp, a], v - 1)
    for _i in range(7):
        sub([a, tmp], v - 1)
    logEnd()


# lines = open("/home/nyancat/Codes/stage0-subleq/phase0-hex/hex0_monitor.msq").read().split("\n")
lines = open(sys.argv[1]).read().split("\n")
for line in lines:
    if len(line.strip()) == 0:
        print()
        continue

    inst = line.split(" ")[0]
    args = line.split(" ")[1:]

    if inst in lsq_insts:
        print(line)
    else:
        if inst == "set":
            inst = "inst_set"
        try:
            globals()[inst](args)
        except KeyError:
            raise SyntaxError(f"Unknown instruction: {inst}")

print()
for const in consts:
    print(f"var CONST_{const:X} {const:x}")
