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
             "decaddr", "setaddr",
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
    return f"CONST_{a:x}"


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
    print(f"relsq 0 0 {a}")


# Jumps to label
def lbljmp(lbl, verbosity=0):
    if verbosity > 0:
        print(f"rem lbljmp {lbl}")
    print(f"lblsq 0 0 {lbl}")


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
    else:
        raise SyntaxError(f"Unknown instruction: {inst}")
