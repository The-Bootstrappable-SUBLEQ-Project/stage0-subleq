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
def sub(a, b, verbosity=0):
    if verbosity > 0:
        print(f"rem sub {a} {b}")
    print(f"relsq {a} {b} 1")


# Sets a to 0
def zero(a, verbosity=0):
    if verbosity > 0:
        print(f"rem zero {a}")
    sub(a, a, verbosity - 1)


# Decreases a by val (Constant)
def dec(a, val, verbosity=0):
    val = ensureInt(val)
    if verbosity > 0:
        print(f"rem dec {a} {val}")
    print(f"relsq {a} {recordConst(val)} 1")


# Decreases a by val (Constant), and jumps to lbl if a <= 0 after operation
def decleq(a, val, lbl, verbosity=0):
    val = ensureInt(val)
    if verbosity > 0:
        print(f"rem decleq {a} {val} {lbl}")
    print(f"lblsq {a} {recordConst(val)} {lbl}")


# Increases a by val (Constant)
def inc(a, val, verbosity=0):
    val = ensureInt(val)
    if verbosity > 0:
        print(f"rem inc {a} {recordConst(val)}")
    dec(a, -val, verbosity - 1)


# Increases a by val (Constant), and jumps to lbl if a <= 0 after operation
def incleq(a, val, lbl, verbosity=0):
    val = ensureInt(val)
    if verbosity > 0:
        print(f"rem incleq {a} {val} {lbl}")
    decleq(a, -val, lbl, verbosity - 1)


# Sets a to val (Constant)
def inst_set(a, val, verbosity=1):
    val = ensureInt(val)
    if verbosity > 0:
        print()
        print(f"rem Start set {a} {val}")
    zero(a, verbosity - 1)
    inc(a, val, verbosity - 1)
    if verbosity > 0:
        print("rem End set")
        print()


# Relatively jumps by a instructions
def reljmp(a, verbosity=0):
    if verbosity > 0:
        print(f"rem reljmp {a}")
    print(f"relsq ZERO ZERO {a}")


# Jumps to label
def lbljmp(lbl, verbosity=0):
    if verbosity > 0:
        print(f"rem lbljmp {lbl}")
    print(f"lblsq ZERO ZERO {lbl}")


# Sets a to -b
def movneg(a, b, verbosity=1):
    if verbosity > 0:
        print(f"rem movneg {a} {b}")
    zero(a, verbosity - 1)
    sub(a, b, verbosity - 1)


# Sets a to b, using tmp as a temporary storage
def mov(a, b, tmp, verbosity=2):
    if verbosity > 0:
        print()
        print(f"rem Start mov {a} {b} {tmp}")
    movneg(tmp, b, verbosity - 1)
    movneg(a, tmp, verbosity - 1)
    if verbosity > 0:
        print("rem End mov")
        print()


# Fetches a character from SERIAL_IN into a, using tmp as a temporary storage
def getchar(a, tmp, verbosity=2):
    if verbosity > 0:
        print()
        print(f"rem Start getchar {a} {tmp}")
    inst_set(tmp, 1, verbosity - 1)
    print(f"relsq {tmp} SERIAL_IN 2")
    reljmp(-1, verbosity - 1)
    zero("SERIAL_IN", verbosity - 1)
    movneg(a, tmp, verbosity - 1)
    if verbosity > 0:
        print("rem End getchar")
        print()


# Outputs a character into SERIAL_IN, using tmp as a temporary storage
def putchar(a, tmp, verbosity=2):
    if verbosity > 0:
        print()
        print(f"rem Start putchar {a} {tmp}")
    print("relsq SERIAL_OUT ZERO 2")
    reljmp(-1, verbosity - 1)
    movneg(tmp, a, verbosity - 1)
    dec(tmp, 1, verbosity - 1)
    movneg("SERIAL_OUT", tmp, verbosity - 1)
    if verbosity > 0:
        print("rem End putchar")
        print()


# Decreases all references of a symbol by b
def decaddr(sym, b, verbosity=0):
    if verbosity > 0:
        print(f"rem decaddr {sym} {b}")
    print(f"subaddr {sym} {recordConst(b)}")


# Sets a to val in one operation, instead of setting it to 0 first
def set_safe(a, val, tmp, tmp2, verbosity=2):
    val = ensureInt(val)
    if verbosity > 0:
        print()
        print(f"rem Start set_safe {a} {val} {tmp} {tmp2}")
    mov(tmp, a, tmp2, verbosity - 1)
    dec(tmp, val, verbosity - 1)
    sub(a, tmp, verbosity - 1)
    if verbosity > 0:
        print("rem End set_safe")
        print()


# Jumps to dst's address if a < b
def jl(a, b, dst, tmp, tmp2, verbosity=2):
    if verbosity > 0:
        print()
        print(f"rem Start jl {a} {b} {dst} {tmp} {tmp2}")
    mov(tmp, a, tmp2, verbosity - 1)
    # Don't jump if a == b
    inc(tmp, 1, verbosity - 1)
    print(f"lblsq {tmp} {b} {dst}")
    if verbosity > 0:
        print("rem End jl")
        print()


# Multiplies a by 16
def mul_16(a, tmp, verbosity=1):
    if verbosity > 0:
        print()
        print(f"rem Start mul_16 {a} {tmp}")
    zero(tmp, verbosity - 1)
    for _i in range(5):
        sub(tmp, a, verbosity - 1)
    for _i in range(3):
        sub(a, tmp, verbosity - 1)
    if verbosity > 0:
        print("rem End mul_16")
        print()


# Multiplies a by 16
def mul_256(a, tmp, verbosity=1):
    if verbosity > 0:
        print()
        print(f"rem Start mul_256 {a} {tmp}")
    mul_16(a, tmp, verbosity - 1)
    mul_16(a, tmp, verbosity - 1)
    if verbosity > 0:
        print("rem End mul_256")
        print()


# Does a = -a
def neg(a, tmp, tmp2, verbosity=1):
    if verbosity > 0:
        print()
        print(f"rem Start neg {a} {tmp} {tmp2}")
    movneg(tmp, a)
    mov(a, tmp, tmp2)
    if verbosity > 0:
        print("rem End neg")
        print()


# lines = open("/home/nyancat/Codes/stage0-subleq/phase0-hex/hex0_monitor.msq").read().split("\n")
lines = open(sys.argv[1]).read().split("\n")
for line in lines:
    if len(line.strip()) == 0:
        print()
        continue

    inst = line.split(" ")[0]
    args = line.split(" ")[1:]
    argc = len(args)

    if inst in lsq_insts:
        print(line)
    elif inst == "sub":
        assert argc == 2
        sub(args[0], args[1])
    elif inst == "zero":
        assert argc == 1
        zero(args[0])
    elif inst == "dec":
        assert argc == 2
        dec(args[0], args[1])
    elif inst == "decleq":
        assert argc == 3
        decleq(args[0], args[1], args[2])
    elif inst == "inc":
        assert argc == 2
        inc(args[0], args[1])
    elif inst == "incleq":
        assert argc == 3
        incleq(args[0], args[1], args[2])
    elif inst == "set":
        assert argc == 2
        inst_set(args[0], args[1])
    elif inst == "reljmp":
        assert argc == 1
        reljmp(args[0])
    elif inst == "lbljmp":
        assert argc == 1
        lbljmp(args[0])
    elif inst == "movneg":
        assert argc == 2
        movneg(args[0], args[1])
    elif inst == "mov":
        assert argc == 3
        mov(args[0], args[1], args[2])
    elif inst == "getchar":
        assert argc == 2
        getchar(args[0], args[1])
    elif inst == "putchar":
        assert argc == 2
        putchar(args[0], args[1])
    elif inst == "decaddr":
        assert argc == 2
        decaddr(args[0], args[1])
    elif inst == "set_safe":
        assert argc == 4
        set_safe(args[0], args[1], args[2], args[3])
    elif inst == "jl":
        assert argc == 5
        jl(args[0], args[1], args[2], args[3], args[4])
    elif inst == "mul_16":
        assert argc == 2
        mul_16(args[0], args[1])
    elif inst == "mul_256":
        assert argc == 2
        mul_256(args[0], args[1])
    elif inst == "neg":
        assert argc == 3
        neg(args[0], args[1], args[2])
    else:
        raise SyntaxError(f"Unknown instruction: {inst}")

print()
for const in consts:
    print(f"var CONST_{const:X} {const:x}")
