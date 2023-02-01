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
             "raw", "raw_ref", "rem"]
consts = []
callCounts = {}


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
    inst = getInstName(frame)
    if inst not in callCounts:
        callCounts[inst] = 0

    if frame.f_locals["v"] > 0:
        print()
        print(f"rem Start {inst} {printArgs(frame.f_locals['args'])}")

    return callCounts[inst]


def logEnd():
    frame = currentframe().f_back
    inst = getInstName(frame)
    if frame.f_locals["v"] > 0:
        print(f"rem End {inst}")
        print()
    callCounts[inst] += 1


# Assigns a unique symbol name for differents calls of an instruction.
# This decreases the performance impact of subaddr/zeroaddr instructions
# by minimizing references to the symbols.
# It also allows for usages of labels inside calls, which makes it easier
# to implement control flow.
def nameSym(suffix, uppercase=False):
    inst = getInstName(currentframe().f_back)
    ret = f"{inst}_{callCounts[inst]}_{suffix}"
    if uppercase:
        ret = ret.upper()
    return ret


# Converts and pads a number to be used in raw instructions
def numToRawInst(num):
    return f"{num:0{16}x}"


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
    logSimple()
    print(f"relsq {a} {recordConst(val)} 1")


# Decreases a by val (Constant), and jumps to lbl if a <= 0 after operation
def decleq(args, v=0):
    a, val, lbl = args
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


# Decreases sym's address by b
def decaddr(args, v=0):
    sym, b = args
    logSimple()
    print(f"subaddr {sym} {recordConst(b)}")


# Increases sym's address by b
def incaddr(args, v=0):
    sym, b = args
    b = ensureInt(b)
    logSimple()
    print(f"subaddr {sym} {recordConst(-b)}")


# Sets a to val in one operation, instead of setting it to 0 first
def set_safe(args, v=2):
    a, val, tmp, tmp2 = args
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


# Jumps to dst's address if a < 0
def jn(args, v=2):
    a, dst, tmp, tmp2 = args
    logSimple()
    jl([a, "ZERO", dst, tmp, tmp2], v - 1)


# Jumps to dst's address if a == 0
def jz(args, v=2):
    a, dst, tmp = args
    logStart()
    revertLabel = nameSym("REVERT_A", True)
    endLabel = nameSym("END", True)

    # Do not jump if a > 0
    movneg([tmp, a], v - 1)
    incleq([tmp, 1, endLabel], v - 1)

    # Do not jump if a < 0
    incleq([a, 1, revertLabel], v - 1)

    # Jump to the label
    dec([a, 1], v - 1)
    lbljmp([dst], v - 1)

    # Revert a to its original value
    print(f"label {revertLabel}")
    dec([a, 1], v - 1)

    print(f"label {endLabel}")
    logEnd()


# Jumps to dst's address if a == b
def jeq(args, v=2):
    a, b, dst, tmp, tmp2 = args
    logStart()
    mov([tmp, a, tmp2], v - 1)
    sub([tmp, b], v - 1)
    jz([tmp, dst, tmp2], v - 1)
    logEnd()


# Jumps to dst's address if a == b, where b is a constant
def jeq_const(args, v=2):
    a, b, dst, tmp, tmp2 = args
    logStart()
    mov([tmp, a, tmp2], v - 1)
    sub([tmp, recordConst(b)], v - 1)
    jz([tmp, dst, tmp2], v - 1)
    logEnd()


# Jumps to dst's address if a != 0
def jnz(args, v=2):
    a, dst, tmp = args
    logStart()
    jumpLabel = nameSym("REVERT_AND_JUMP", True)
    endLabel = nameSym("END", True)

    # Jump if a > 0
    movneg([tmp, a], v - 1)
    incleq([tmp, 1, dst], v - 1)

    # Jump if a < 0
    incleq([a, 1, jumpLabel], v - 1)

    # Revert a to its original value, but don't jump
    dec([a, 1], v - 1)
    lbljmp([endLabel], v - 1)

    # Revert a to its original value, then jump
    print(f"label {jumpLabel}")
    dec([a, 1], v - 1)
    lbljmp([dst], v - 1)

    print(f"label {endLabel}")
    logEnd()


# Jumps to dst's address if a != b
def jne(args, v=2):
    a, b, dst, tmp, tmp2 = args
    logStart()
    mov([tmp, a, tmp2], v - 1)
    sub([tmp, b], v - 1)
    jnz([tmp, dst, tmp2], v - 1)
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


# Allocates size bytes of buffer, and sets a's value to the address
# Freeing of memory is currently not supported
def malloc(args, v=1):
    a, size, tmp = args
    logStart()
    mov([a, "FREE_START", tmp], v - 1)
    add(["FREE_START", size, tmp], v - 1)
    logEnd()


# Works just like malloc, except that size is a constant
def malloc_const(args, v=1):
    a, size, tmp = args
    logStart()
    malloc([a, recordConst(size), tmp], v - 1)
    logEnd()


# Creates a string on a.
# a must be at least 24 bytes in size to prevent overwriting
# A string is made out of three parts:
# 1. Address of the string's buffer
# 2. Length of the string
# 3. Capacity of the buffer
# See also: https://doc.rust-lang.org/std/string/struct.String.html#representation
def alloc_str(args, v=2):
    a, capacity, tmp = args
    logStart()
    malloc_const([a, capacity, tmp])

    incaddr([a, 8], v - 1)
    zero([a], v - 1)

    incaddr([a, 8], v - 1)
    mov([a, recordConst(capacity), tmp], v - 1)

    decaddr([a, 16], v - 1)
    logEnd()


# Reads serial input into string a until space, \r, or \n is fed
# It also ignores space, \r, or \n characters fed at the beginning, if any
# No capacity check has been implemented yet
def inp_token(args, v=2):
    a, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP")
    termLabel = nameSym("TERM")

    strName = nameSym("str")
    print(f"addr {strName} 0")
    setaddr([strName, a, tmp], v - 1)

    lenName = nameSym("len")
    print(f"var {lenName} 0")
    zero([lenName], v - 1)

    print(f"label {loopLabel}")
    getchar([strName, tmp], v - 1)
    jeq_const([strName, ord(" "), termLabel, tmp, tmp2], v - 1)
    jeq_const([strName, ord("\r"), termLabel, tmp, tmp2], v - 1)
    jeq_const([strName, ord("\n"), termLabel, tmp, tmp2], v - 1)

    inc([lenName, 1], v - 1)
    incaddr([strName, 8], v - 1)
    lbljmp([loopLabel], v - 1)

    print(f"label {termLabel}")
    # Return to the loop if no bytes have been fed yet
    decleq([lenName, 0, loopLabel], v - 1)

    # Set a's length
    incaddr([a, 8], v - 1)
    mov([a, lenName, tmp], v - 1)
    decaddr([a, 8], v - 1)
    logEnd()


# Reads serial input into string a until \r or \n is fed
# If a \r or \n is hit right at the beginning, the string will remain empty
# No capacity check has been implemented yet
def inp_line(args, v=2):
    a, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP")
    termLabel = nameSym("TERM")

    strName = nameSym("str")
    print(f"addr {strName} 0")
    setaddr([strName, a, tmp], v - 1)

    lenName = nameSym("len")
    print(f"var {lenName} 0")
    zero([lenName], v - 1)

    print(f"label {loopLabel}")
    getchar([strName, tmp], v - 1)
    jeq_const([strName, ord("\r"), termLabel, tmp, tmp2], v - 1)
    jeq_const([strName, ord("\n"), termLabel, tmp, tmp2], v - 1)

    inc([lenName, 1], v - 1)
    incaddr([strName, 8], v - 1)
    lbljmp([loopLabel], v - 1)

    print(f"label {termLabel}")

    # Set a's length
    incaddr([a, 8], v - 1)
    mov([a, lenName, tmp], v - 1)
    decaddr([a, 8], v - 1)
    logEnd()


# Outputs the full content of string a
def puts(args, v=2):
    a, tmp = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    endLabel = nameSym("END", True)

    strName = nameSym("str")
    print(f"addr {strName} 0")
    setaddr([strName, a, tmp], v - 1)

    lenName = nameSym("len")
    print(f"var {lenName} 0 ")
    incaddr([a, 8], v - 1)
    mov([lenName, a, tmp], v - 1)
    decaddr([a, 8], v - 1)

    print(f"label {loopLabel}")

    decleq([lenName, 0, endLabel], v - 1)
    dec([lenName, 1], v - 1)

    putchar([strName, tmp], v - 1)
    incaddr([strName, 8], v - 1)
    lbljmp([loopLabel], v - 1)

    print(f"label {endLabel}")
    logEnd()


# Places a sequence of ASCII characters in the memory
# Everything after "raw_chars " and before the newline are considered part of the string.
# Escape character (\) is not handled.
def raw_chars(args, v=1):
    assert len(args) != 0
    logSimple()
    chars = [numToRawInst(ord(x)) for x in " ".join(args)]
    print(f"raw {' '.join(chars)}")


# Places a well-structured string in the memory
# The first argument is used to name the symbol, every other arguments go as part of the string.
def def_string(args, v=1):
    assert len(args) > 1
    logStart()
    sym = args[0]
    string = " ".join(args[1:])
    print(f"label {sym}_buf")
    raw_chars([string], v - 1)
    print(f"label {sym}")
    print(f"raw_ref {sym}_buf")
    print(f"raw {numToRawInst(len(string))} {numToRawInst(len(string) * 8)}")


# Checks if string a and b are:
# 1. Of the same length
# 2. Of the same content
# If both checks pass, it jumps to dst.
def strcmp(args, v=3):
    a, b, dst, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    revertLabel = nameSym("REVERT_ADDR", True)
    endLabel = nameSym("END", True)

    incaddr([a, 8], v - 1)
    incaddr([b, 8], v - 1)
    # Don't jump if a.length != b.length
    jne([a, b, revertLabel, tmp, tmp2], v - 1)

    lenName = nameSym("len")
    print(f"var {lenName} 0")
    mov([lenName, a, tmp], v - 1)
    decaddr([a, 8], v - 1)
    decaddr([b, 8], v - 1)

    aStr = nameSym("aStr")
    bStr = nameSym("bStr")
    print(f"addr {aStr} 0")
    print(f"addr {bStr} 0")
    setaddr([aStr, a, tmp], v - 1)
    setaddr([bStr, b, tmp], v - 1)

    print(f"label {loopLabel}")
    # Jump if all bytes match
    decleq([lenName, 0, dst], v - 1)
    dec([lenName, 1], v - 1)

    # Don't jump if a byte mismatches
    jne([aStr, bStr, endLabel, tmp, tmp2], v - 1)
    incaddr([aStr, 8], v - 1)
    incaddr([bStr, 8], v - 1)
    lbljmp([loopLabel], v - 1)

    print(f"label {revertLabel}")
    decaddr([a, 8], v - 1)
    decaddr([b, 8], v - 1)

    print(f"label {endLabel}")
    logEnd()


# Does a %= 256
def mod_256(args, v=3):
    a, tmp, tmp2 = args
    logStart()
    startLabel = nameSym("START", True)
    endLabel = nameSym("END", True)
    isNegLabel = nameSym("IS_NEG", True)
    checkNegLabel = nameSym("CHECK_NEG", True)
    multSubberStartLabel = nameSym("MULT_SUBBER_START", True)
    subtractALabel = nameSym("SUBTRACT_A", True)

    # Negate if a < 0
    isNeg = nameSym("isNeg")
    print(f"var {isNeg} 0")
    zero([isNeg], v - 1)
    jn([a, isNegLabel, tmp, tmp2], v - 1)
    lbljmp([startLabel], v - 1)

    print(f"label {isNegLabel}")
    inc([isNeg, 1], v - 1)
    neg([a, tmp, tmp2], v - 1)

    print(f"label {startLabel}")
    subber = nameSym("subber")
    print(f"var {subber} 0")
    inst_set([subber, 0x100], v - 1)

    # Finish if a < 0x100
    jl([a, subber, checkNegLabel, tmp, tmp2], v - 1)

    # Multiply subbers by 0x100 until the next multiplication makes subber > a
    nextSubber = nameSym("nextSubber")
    print(f"var {nextSubber} 0")
    inst_set([nextSubber, 0x10000], v - 1)

    print(f"label {multSubberStartLabel}")
    jl([a, nextSubber, subtractALabel, tmp, tmp2], v - 1)
    mul_256([subber, tmp], v - 1)
    mul_256([nextSubber, tmp], v - 1)
    # nextSubber overflowed
    decleq([nextSubber, 0, subtractALabel], v - 1)
    lbljmp([multSubberStartLabel], v - 1)

    # Subtract a by subber until the next subtraction makes a < 0
    print(f"label {subtractALabel}")
    jl([a, subber, startLabel, tmp, tmp2], v - 1)
    sub([a, subber], v - 1)
    lbljmp([subtractALabel], v - 1)

    print(f"label {checkNegLabel}")
    decleq([isNeg, 0, endLabel], v - 1)
    # No need to invert if a == 0
    decleq([a, 0, endLabel], v - 1)
    # rem c = 256 - c
    mov([tmp, a, tmp2], v - 1)
    inst_set([a, 0x100], v - 1)
    sub([a, tmp], v - 1)

    print(f"label {endLabel}")


def halt(args, v=2):
    tmp, tmp2 = args
    logStart()
    # Stop CPU 0
    set_safe(["CPU_CONTROL_START", 2, tmp, tmp2], v - 1)
    # Infinite loop
    print("relsq ZERO ZERO 0")


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

print()
print("end")
