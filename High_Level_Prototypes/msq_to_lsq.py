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


# Subtracts a by b
def sub(args, verbosity=0):
    a, b = args
    if verbosity > 0:
        print(f"rem sub {a} {b}")
    print(f"relsq {a} {b} 1")


# Sets a to 0
def zero(args, verbosity=0):
    assert len(args) == 1
    a = args[0]
    if verbosity > 0:
        print(f"rem zero {a}")
    sub([a, a], verbosity - 1)


# Decreases a by val (Constant)
def dec(args, verbosity=0):
    a, val = args
    val = ensureInt(val)
    if verbosity > 0:
        print(f"rem dec {a} {val}")
    print(f"relsq {a} {recordConst(val)} 1")


# Decreases a by val (Constant), and jumps to lbl if a <= 0 after operation
def decleq(args, verbosity=0):
    a, val, lbl = args
    val = ensureInt(val)
    if verbosity > 0:
        print(f"rem decleq {a} {val} {lbl}")
    print(f"lblsq {a} {recordConst(val)} {lbl}")


# Increases a by val (Constant)
def inc(args, verbosity=0):
    a, val = args
    val = ensureInt(val)
    if verbosity > 0:
        print(f"rem inc {a} {recordConst(val)}")
    dec([a, -val], verbosity - 1)


# Increases a by val (Constant), and jumps to lbl if a <= 0 after operation
def incleq(args, verbosity=0):
    a, val, lbl = args
    val = ensureInt(val)
    if verbosity > 0:
        print(f"rem incleq {a} {val} {lbl}")
    decleq([a, -val, lbl], verbosity - 1)


# Sets a to val (Constant)
def inst_set(args, verbosity=1):
    a, val = args
    val = ensureInt(val)
    if verbosity > 0:
        print()
        print(f"rem Start set {a} {val}")
    zero([a], verbosity - 1)
    inc([a, val], verbosity - 1)
    if verbosity > 0:
        print("rem End set")
        print()


# Relatively jumps by a instructions
def reljmp(args, verbosity=0):
    assert len(args) == 1
    a = args[0]
    if verbosity > 0:
        print(f"rem reljmp {a}")
    print(f"relsq ZERO ZERO {a}")


# Jumps to a label
def lbljmp(args, verbosity=0):
    assert len(args) == 1
    lbl = args[0]
    if verbosity > 0:
        print(f"rem lbljmp {lbl}")
    print(f"lblsq ZERO ZERO {lbl}")


# Sets a to -b
def movneg(args, verbosity=1):
    a, b = args
    if verbosity > 0:
        print(f"rem movneg {a} {b}")
    zero([a], verbosity - 1)
    sub([a, b], verbosity - 1)


# Sets a to b, using tmp as a temporary storage
def mov(args, verbosity=2):
    a, b, tmp = args
    if verbosity > 0:
        print()
        print(f"rem Start mov {a} {b} {tmp}")
    movneg([tmp, b], verbosity - 1)
    movneg([a, tmp], verbosity - 1)
    if verbosity > 0:
        print("rem End mov")
        print()


# Fetches a character from SERIAL_IN into a, using tmp as a temporary storage
def getchar(args, verbosity=2):
    a, tmp = args
    if verbosity > 0:
        print()
        print(f"rem Start getchar {a} {tmp}")
    inst_set([tmp, 1], verbosity - 1)
    print(f"relsq {tmp} SERIAL_IN 2")
    reljmp([-1], verbosity - 1)
    zero(["SERIAL_IN"], verbosity - 1)
    movneg([a, tmp], verbosity - 1)
    if verbosity > 0:
        print("rem End getchar")
        print()


# Outputs a character into SERIAL_IN, using tmp as a temporary storage
def putchar(args, verbosity=2):
    a, tmp = args
    if verbosity > 0:
        print()
        print(f"rem Start putchar {a} {tmp}")
    print("relsq SERIAL_OUT ZERO 2")
    reljmp([-1], verbosity - 1)
    movneg([tmp, a], verbosity - 1)
    dec([tmp, 1], verbosity - 1)
    movneg(["SERIAL_OUT", tmp], verbosity - 1)
    if verbosity > 0:
        print("rem End putchar")
        print()


# Decreases all references of a symbol by b
def decaddr(args, verbosity=0):
    sym, b = args
    if verbosity > 0:
        print(f"rem decaddr {sym} {b}")
    print(f"subaddr {sym} {recordConst(b)}")


# Sets a to val in one operation, instead of setting it to 0 first
def set_safe(args, verbosity=2):
    a, val, tmp, tmp2 = args
    val = ensureInt(val)
    if verbosity > 0:
        print()
        print(f"rem Start set_safe {a} {val} {tmp} {tmp2}")
    mov([tmp, a, tmp2], verbosity - 1)
    dec([tmp, val], verbosity - 1)
    sub([a, tmp], verbosity - 1)
    if verbosity > 0:
        print("rem End set_safe")
        print()


# Jumps to dst's address if a < b
def jl(args, verbosity=2):
    a, b, dst, tmp, tmp2 = args
    if verbosity > 0:
        print()
        print(f"rem Start jl {a} {b} {dst} {tmp} {tmp2}")
    mov([tmp, a, tmp2], verbosity - 1)
    # Don't jump if a == b
    inc([tmp, 1], verbosity - 1)
    print(f"lblsq {tmp} {b} {dst}")
    if verbosity > 0:
        print("rem End jl")
        print()


# Multiplies a by 16
def mul_16(args, verbosity=1):
    a, tmp = args
    if verbosity > 0:
        print()
        print(f"rem Start mul_16 {a} {tmp}")
    zero([tmp], verbosity - 1)
    for _i in range(5):
        sub([tmp, a], verbosity - 1)
    for _i in range(3):
        sub([a, tmp], verbosity - 1)
    if verbosity > 0:
        print("rem End mul_16")
        print()


# Multiplies a by 16
def mul_256(args, verbosity=1):
    a, tmp = args
    if verbosity > 0:
        print()
        print(f"rem Start mul_256 {a} {tmp}")
    mul_16([a, tmp], verbosity - 1)
    mul_16([a, tmp], verbosity - 1)
    if verbosity > 0:
        print("rem End mul_256")
        print()


# Does a = -a
def neg(args, verbosity=1):
    a, tmp, tmp2 = args
    if verbosity > 0:
        print()
        print(f"rem Start neg {a} {tmp} {tmp2}")
    movneg([tmp, a], verbosity - 1)
    mov([a, tmp, tmp2], verbosity - 1)
    if verbosity > 0:
        print("rem End neg")
        print()


# Sets the address of sym to the value of val
def setaddr(args, verbosity=2):
    sym, val, tmp = args
    if verbosity > 0:
        print()
        print(f"rem Start setaddr {sym} {val} {tmp}")
    print(f"zeroaddr {sym}")
    movneg([tmp, val], verbosity - 1)
    print(f"subaddr {sym} {tmp}")
    if verbosity > 0:
        print("rem End setaddr")
        print()


# Does a += b
def add(args, verbosity=2):
    a, b, tmp = args
    if verbosity > 0:
        print()
        print(f"rem Start add {a} {b} {tmp}")
    movneg([tmp, b], verbosity - 1)
    sub([a, tmp], verbosity - 1)
    if verbosity > 0:
        print("rem End add")
        print()


# Does a *= 8
def mul_8(args, verbosity=1):
    a, tmp = args
    if verbosity > 0:
        print()
        print(f"rem Start mul_8 {a} {tmp}")
    movneg([tmp, a], verbosity - 1)
    for _i in range(7):
        sub([a, tmp], verbosity - 1)
    if verbosity > 0:
        print("rem end mul_8")
        print()


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
