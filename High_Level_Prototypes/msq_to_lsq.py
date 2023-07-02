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
import ctypes
import argparse

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


depth = 0


def logStart():
    global depth
    frame = currentframe().f_back
    inst = getInstName(frame)
    if inst not in callCounts:
        callCounts[inst] = 0

    if depth < verbosity:
        print(f"rem MSQ_START {depth} {inst} {printArgs(frame.f_locals['args'])}")

    depth += 1


def logEnd():
    global depth
    depth -= 1

    frame = currentframe().f_back
    inst = getInstName(frame)
    if depth < verbosity:
        print(f"rem MSQ_END {depth} {inst}")

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
    # "__ctype_be__ Python" have 349 results on Google, smh
    return bytearray(ctypes.c_long.__ctype_be__(num)).hex()


# Subtracts a by b
def sub(args):
    a, b = args
    logStart()
    print(f"relsq {a} {b} 1")
    logEnd()


# Sets a to 0
def zero(args):
    assert len(args) == 1
    a = args[0]
    logStart()
    sub([a, a])
    logEnd()


# Decreases a by val (Constant)
def dec(args):
    a, val = args
    logStart()
    print(f"relsq {a} {recordConst(val)} 1")
    logEnd()


# Decreases a by val (Constant), and jumps to lbl if a <= 0 after operation
def decleq(args):
    a, val, lbl = args
    logStart()
    print(f"lblsq {a} {recordConst(val)} {lbl}")
    logEnd()


# Increases a by val (Constant)
def inc(args):
    a, val = args
    val = ensureInt(val)
    logStart()
    dec([a, -val])
    logEnd()


# Increases a by val (Constant), and jumps to lbl if a <= 0 after operation
def incleq(args):
    a, val, lbl = args
    val = ensureInt(val)
    logStart()
    decleq([a, -val, lbl])
    logEnd()


# Sets a to val (Constant)
def inst_set(args):
    a, val = args
    logStart()
    zero([a])
    inc([a, val])
    logEnd()


# Relatively jumps by a instructions
def reljmp(args):
    assert len(args) == 1
    a = args[0]
    logStart()
    print(f"relsq ZERO ZERO {a}")
    logEnd()


# Jumps to a label
def lbljmp(args):
    assert len(args) == 1
    lbl = args[0]
    logStart()
    print(f"lblsq ZERO ZERO {lbl}")
    logEnd()


# Sets a to -b
def movneg(args):
    a, b = args
    logStart()
    zero([a])
    sub([a, b])
    logEnd()


# Sets a to b, using tmp as a temporary storage
def mov(args):
    a, b, tmp = args
    logStart()
    movneg([tmp, b])
    movneg([a, tmp])
    logEnd()


# Fetches a character from SERIAL_IN into a, using tmp as a temporary storage
def getchar(args):
    a, tmp = args
    logStart()
    inst_set([tmp, 1])
    print(f"relsq {tmp} SERIAL_IN 2")
    reljmp([-1])
    zero(["SERIAL_IN"])
    movneg([a, tmp])
    logEnd()


# Outputs a character into SERIAL_IN, using tmp as a temporary storage
def putchar(args):
    a, tmp = args
    logStart()
    print("relsq SERIAL_OUT ZERO 2")
    reljmp([-1])
    movneg([tmp, a])
    dec([tmp, 1])
    movneg(["SERIAL_OUT", tmp])
    logEnd()


# Decreases sym's address by b
def decaddr(args):
    sym, b = args
    logStart()
    print(f"subaddr {sym} {recordConst(b)}")
    logEnd()


# Increases sym's address by b
def incaddr(args):
    sym, b = args
    b = ensureInt(b)
    logStart()
    print(f"subaddr {sym} {recordConst(-b)}")
    logEnd()


# Sets a to val in one operation, instead of setting it to 0 first
def set_safe(args):
    a, val, tmp, tmp2 = args
    logStart()
    mov([tmp, a, tmp2])
    dec([tmp, val])
    sub([a, tmp])
    logEnd()


# Jumps to dst's address if a < b
def jl(args):
    a, b, dst, tmp, tmp2 = args
    logStart()
    mov([tmp, a, tmp2])
    # Don't jump if a == b
    inc([tmp, 1])
    print(f"lblsq {tmp} {b} {dst}")
    logEnd()


# Jumps to dst's address if a < 0
def jn(args):
    a, dst, tmp, tmp2 = args
    logStart()
    jl([a, "ZERO", dst, tmp, tmp2])
    logEnd()


# Jumps to dst's address if a == 0
def jz(args):
    a, dst, tmp = args
    logStart()
    revertLabel = nameSym("REVERT_A", True)
    endLabel = nameSym("END", True)

    # Do not jump if a > 0
    movneg([tmp, a])
    incleq([tmp, 1, endLabel])

    # Do not jump if a < 0
    incleq([a, 1, revertLabel])

    # Jump to the label
    dec([a, 1])
    lbljmp([dst])

    # Revert a to its original value
    print(f"label {revertLabel}")
    dec([a, 1])

    print(f"label {endLabel}")
    logEnd()


# Jumps to dst's address if a == b
def jeq(args):
    a, b, dst, tmp, tmp2 = args
    logStart()
    mov([tmp, a, tmp2])
    sub([tmp, b])
    jz([tmp, dst, tmp2])
    logEnd()


# Jumps to dst's address if a == b, where b is a constant
def jeq_const(args):
    a, b, dst, tmp, tmp2 = args
    logStart()
    mov([tmp, a, tmp2])
    sub([tmp, recordConst(b)])
    jz([tmp, dst, tmp2])
    logEnd()


# Jumps to dst's address if a != 0
def jnz(args):
    a, dst, tmp = args
    logStart()
    jumpLabel = nameSym("REVERT_AND_JUMP", True)
    endLabel = nameSym("END", True)

    # Jump if a > 0
    movneg([tmp, a])
    incleq([tmp, 1, dst])

    # Jump if a < 0
    incleq([a, 1, jumpLabel])

    # Revert a to its original value, but don't jump
    dec([a, 1])
    lbljmp([endLabel])

    # Revert a to its original value, then jump
    print(f"label {jumpLabel}")
    dec([a, 1])
    lbljmp([dst])

    print(f"label {endLabel}")
    logEnd()


# Jumps to dst's address if a != b
def jne(args):
    a, b, dst, tmp, tmp2 = args
    logStart()
    mov([tmp, a, tmp2])
    sub([tmp, b])
    jnz([tmp, dst, tmp2])
    logEnd()


# Multiplies a by 16
def mul_16(args):
    a, tmp = args
    logStart()
    zero([tmp])
    for _i in range(5):
        sub([tmp, a])
    for _i in range(3):
        sub([a, tmp])
    logEnd()


# Multiplies a by 256
def mul_256(args):
    a, tmp = args
    logStart()
    mul_16([a, tmp])
    mul_16([a, tmp])
    logEnd()


# Does a = -a
def neg(args):
    a, tmp, tmp2 = args
    logStart()
    movneg([tmp, a])
    mov([a, tmp, tmp2])
    logEnd()


# Increases the address of sym by the value of val
def addaddr(args):
    sym, val, tmp = args
    logStart()
    movneg([tmp, val])
    print(f"subaddr {sym} {tmp}")
    logEnd()


# Sets the address of sym to the value of val
def setaddr(args):
    sym, val, tmp, tmp2 = args
    logStart()
    addrRef = f"{sym}_addrRef_0"
    mov([tmp, addrRef, tmp2])
    sub([tmp, val])
    print(f"subaddr {sym} {tmp}")
    logEnd()


# Sets the address of toSym to the address of fromSym
def copyaddr(args):
    toSym, fromSym, tmp, tmp2 = args
    logStart()
    addrRef = f"{fromSym}_addrRef_0"
    setaddr([toSym, addrRef, tmp, tmp2])
    logEnd()


# Does a += b
def add(args):
    a, b, tmp = args
    logStart()
    movneg([tmp, b])
    sub([a, tmp])
    logEnd()


# Does a *= 8
def mul_8(args):
    a, tmp = args
    logStart()
    movneg([tmp, a])
    for _i in range(7):
        sub([a, tmp])
    logEnd()


# Allocates size bytes of buffer, and sets a's value to the address
# Freeing of memory is currently not supported
def malloc(args):
    a, size, tmp = args
    logStart()
    mov([a, "FREE_START", tmp])
    add(["FREE_START", size, tmp])
    logEnd()


# Works just like malloc, except that size is a constant
def malloc_const(args):
    a, size, tmp = args
    logStart()
    malloc([a, recordConst(size), tmp])
    logEnd()


# Creates a string on a.
# a must be at least 24 bytes in size to prevent overwriting
# A string is made out of three parts:
# 1. Address to the string's buffer
# 2. Length of the string in characters
# 3. Capacity of the buffer in bytes
# See also: https://doc.rust-lang.org/std/string/struct.String.html#representation
def alloc_str(args):
    a, capacity, tmp = args
    logStart()
    malloc([a, capacity, tmp])

    incaddr([a, 8])
    zero([a])

    incaddr([a, 8])
    mov([a, capacity, tmp])

    decaddr([a, 16])
    logEnd()


# Works just like alloc_str, except that capacity is a constant
def alloc_str_const(args):
    a, capacity, tmp = args
    logStart()
    malloc_const([a, capacity, tmp])

    incaddr([a, 8])
    zero([a])

    incaddr([a, 8])
    mov([a, recordConst(capacity), tmp])

    decaddr([a, 16])
    logEnd()


# Creates an array on a.
# a must be at least 32 bytes in size to prevent overwriting
# An array is made out of four parts:
# 1. Address to the array's buffer
# 2. Number of elements in the array
# 3. Size of every element in the array
# 4. Capacity of the buffer in bytes
def alloc_array(args):
    a, elmSize, maxElms, tmp = args
    logStart()
    elmSize = ensureInt(elmSize)
    maxElms = ensureInt(maxElms)
    capacity = elmSize * maxElms
    malloc_const([a, capacity, tmp])

    incaddr([a, 8])
    zero([a])

    incaddr([a, 8])
    mov([a, recordConst(elmSize), tmp])

    incaddr([a, 8])
    mov([a, recordConst(capacity), tmp])

    decaddr([a, 24])
    logEnd()


# Reads serial input into string a until space, \r, or \n is fed
# It also ignores space, \r, or \n characters fed at the beginning, if any
# No capacity check has been implemented yet
def inp_token(args):
    a, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    termLabel = nameSym("TERM", True)

    strName = nameSym("str")
    print(f"addr {strName} 0")
    setaddr([strName, a, tmp, tmp2])

    lenName = nameSym("len")
    print(f"var {lenName} 0")
    zero([lenName])

    print(f"label {loopLabel}")
    getchar([strName, tmp])
    jeq_const([strName, ord(" "), termLabel, tmp, tmp2])
    jeq_const([strName, ord("\r"), termLabel, tmp, tmp2])
    jeq_const([strName, ord("\n"), termLabel, tmp, tmp2])

    inc([lenName, 1])
    incaddr([strName, 8])
    lbljmp([loopLabel])

    print(f"label {termLabel}")
    # Return to the loop if no bytes have been fed yet
    decleq([lenName, 0, loopLabel])

    # Set a's length
    incaddr([a, 8])
    mov([a, lenName, tmp])
    decaddr([a, 8])
    logEnd()


# Reads serial input into string a until space, \r, or \n is fed
# When a space, \r, or \n character is fed at the beginning, it returns an empty string.
# No capacity check has been implemented yet
def inp_token_allow_empty(args):
    a, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    termLabel = nameSym("TERM", True)

    strName = nameSym("str")
    print(f"addr {strName} 0")
    setaddr([strName, a, tmp, tmp2])

    lenName = nameSym("len")
    print(f"var {lenName} 0")
    zero([lenName])

    print(f"label {loopLabel}")
    getchar([strName, tmp])
    jeq_const([strName, ord(" "), termLabel, tmp, tmp2])
    jeq_const([strName, ord("\r"), termLabel, tmp, tmp2])
    jeq_const([strName, ord("\n"), termLabel, tmp, tmp2])

    inc([lenName, 1])
    incaddr([strName, 8])
    lbljmp([loopLabel])

    print(f"label {termLabel}")
    # Set a's length
    incaddr([a, 8])
    mov([a, lenName, tmp])
    decaddr([a, 8])
    logEnd()


# Reads serial input into string a until \r or \n is fed
# If a \r or \n is hit right at the beginning, the string will remain empty
# No capacity check has been implemented yet
def inp_line(args):
    a, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    termLabel = nameSym("TERM", True)

    strName = nameSym("str")
    print(f"addr {strName} 0")
    setaddr([strName, a, tmp, tmp2])

    lenName = nameSym("len")
    print(f"var {lenName} 0")
    zero([lenName])

    print(f"label {loopLabel}")
    getchar([strName, tmp])
    jeq_const([strName, ord("\r"), termLabel, tmp, tmp2])
    jeq_const([strName, ord("\n"), termLabel, tmp, tmp2])

    inc([lenName, 1])
    incaddr([strName, 8])
    lbljmp([loopLabel])

    print(f"label {termLabel}")

    # Set a's length
    incaddr([a, 8])
    mov([a, lenName, tmp])
    decaddr([a, 8])
    logEnd()


# Copies the content of string b to string a
# No capacity check has been implemented yet
def strcpy(args):
    a, b, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    endLabel = nameSym("END", True)

    strA = nameSym("strA")
    print(f"addr {strA} 0")
    setaddr([strA, a, tmp, tmp2])

    strB = nameSym("strB")
    print(f"addr {strB} 0")
    setaddr([strB, b, tmp, tmp2])

    # Copy and store the string length
    incaddr([a, 8])
    incaddr([b, 8])
    mov([a, b, tmp])
    strLen = nameSym("strLen")
    print(f"var {strLen} 0")
    mov([strLen, b, tmp])
    decaddr([a, 8])
    decaddr([b, 8])

    # Copy the string buffer
    print(f"label {loopLabel}")
    decleq([strLen, 0, endLabel])
    dec([strLen, 1])
    mov([strA, strB, tmp])
    incaddr([strA, 8])
    incaddr([strB, 8])
    lbljmp([loopLabel])

    print(f"label {endLabel}")
    logEnd()


# Splits a string by a single-character delimiter and stores the split parts in the a array.
# No checks are performed on a's capacity or the partCapacity.
def str_split(args):
    a, string, delim, partCapacity, tmp, tmp2 = args
    partCapacity = ensureInt(partCapacity)
    logStart()

    partLooplabel = nameSym("PART_LOOP", True)
    charLoopLabel = nameSym("CHAR_LOOP", True)
    endPart = nameSym("END_PART", True)
    endSplit = nameSym("END_SPLIT", True)

    aBuf = nameSym("aBuf")
    print(f"addr {aBuf} 0")
    setaddr([aBuf, a, tmp, tmp2])

    strBuf = nameSym("strBuf")
    print(f"addr {strBuf} 0")
    setaddr([strBuf, string, tmp, tmp2])

    charsLeft = nameSym("charsLeft")
    print(f"var {charsLeft} 0")
    incaddr([string, 8])
    mov([charsLeft, string, tmp])
    decaddr([string, 8])

    partCount = nameSym("partCount")
    print(f"var {partCount} 0")
    zero([partCount])

    print(f"label {partLooplabel}")
    decleq([charsLeft, 0, endSplit])
    # Allocate a new part
    alloc_str_const([aBuf, partCapacity, tmp])
    inc([partCount, 1])
    partLen = nameSym("partLen")
    print(f"var {partLen} 0")
    zero([partLen])

    partBuf = nameSym("partBuf")
    print(f"addr {partBuf} 0")
    setaddr([partBuf, aBuf, tmp, tmp2])

    print(f"label {charLoopLabel}")
    # End the char loop if there are no chars left
    decleq([charsLeft, 0, endPart])
    dec([charsLeft, 1])

    # Fetch next character and end the loop if it's the delim
    curChar = nameSym("curChar")
    print(f"var {curChar} 0")
    mov([curChar, strBuf, tmp])
    incaddr([strBuf, 8])
    jeq([curChar, delim, endPart, tmp, tmp2])

    # Copy the character to the part
    mov([partBuf, curChar, tmp])
    incaddr([partBuf, 8])
    inc([partLen, 1])
    lbljmp([charLoopLabel])

    print(f"label {endPart}")
    # Set the part's length
    incaddr([aBuf, 8])
    mov([aBuf, partLen, tmp])

    incaddr([aBuf, 16])
    lbljmp([partLooplabel])

    print(f"label {endSplit}")
    # Set the array's length
    incaddr([a, 8])
    mov([a, partCount, tmp])
    decaddr([a, 8])
    logEnd()


# Outputs the full content of string a
def puts(args):
    a, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    endLabel = nameSym("END", True)

    strName = nameSym("str")
    print(f"addr {strName} 0")
    setaddr([strName, a, tmp, tmp2])

    lenName = nameSym("len")
    print(f"var {lenName} 0")
    incaddr([a, 8])
    mov([lenName, a, tmp])
    decaddr([a, 8])

    print(f"label {loopLabel}")

    decleq([lenName, 0, endLabel])
    dec([lenName, 1])

    putchar([strName, tmp])
    incaddr([strName, 8])
    lbljmp([loopLabel])

    print(f"label {endLabel}")
    logEnd()


# Places a sequence of ASCII characters in the memory
# Everything after "raw_chars " and before the newline are considered part of the string.
# Escape character (\) is not handled.
def raw_chars(args):
    assert len(args) != 0
    logStart()
    string = " ".join(args)
    if len(string) != 0:
        chars = [numToRawInst(ord(x)) for x in string]
        print(f"raw {' '.join(chars)}")
    else:
        print("rem This is an empty string")
    logEnd()


# Places a well-structured string in the memory
# The first argument is used to name the symbol, every other arguments go as part of the string.
def def_string(args):
    assert len(args) > 1
    logStart()
    sym = args[0]
    string = " ".join(args[1:])
    print(f"label {sym}_BUF")
    raw_chars([string])
    print(f"label {sym}")
    print(f"raw_ref {sym}_BUF")
    print(f"raw {numToRawInst(len(string))} {numToRawInst(len(string) * 8)}")
    logEnd()


# Checks if string orgA and orgB are:
# 1. Of the same length
# 2. Of the same content
# If both checks pass, it jumps to dst.
def strcmp(args):
    orgA, orgB, dst, tmp, tmp2 = args
    logStart()
    b = nameSym("b")
    print(f"addr {b} 0")
    copyaddr([b, orgB, tmp, tmp2])
    strcmp_const([orgA, b, dst, tmp, tmp2])
    logEnd()


# Same as strcmp, except that it doesn't run copyaddr on b
def strcmp_const(args):
    orgA, b, dst, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    revertLabel = nameSym("REVERT_ADDR", True)
    endLabel = nameSym("END", True)

    a = nameSym("a")
    print(f"addr {a} 0")
    copyaddr([a, orgA, tmp, tmp2])

    incaddr([a, 8])
    incaddr([b, 8])
    # Don't jump if a.length != b.length
    jne([a, b, revertLabel, tmp, tmp2])

    lenName = nameSym("len")
    print(f"var {lenName} 0")
    mov([lenName, a, tmp])
    decaddr([a, 8])
    decaddr([b, 8])

    aStr = nameSym("aStr")
    bStr = nameSym("bStr")
    print(f"addr {aStr} 0")
    print(f"addr {bStr} 0")
    setaddr([aStr, a, tmp, tmp2])
    setaddr([bStr, b, tmp, tmp2])

    print(f"label {loopLabel}")
    # Jump if all bytes match
    decleq([lenName, 0, dst])
    dec([lenName, 1])

    # Don't jump if a byte mismatches
    jne([aStr, bStr, endLabel, tmp, tmp2])
    incaddr([aStr, 8])
    incaddr([bStr, 8])
    lbljmp([loopLabel])

    print(f"label {revertLabel}")
    # decaddr([a, 8])
    decaddr([b, 8])

    print(f"label {endLabel}")
    logEnd()


# Sets a's value to string's length
def strlen(args):
    a, string, tmp = args
    logStart()
    incaddr([string, 8])
    mov([a, string, tmp])
    decaddr([string, 8])
    logEnd()


# Allocates a string on ret and sets its content to strA + strB
def strcat(args):
    ret, strA, strB, tmp, tmp2, tmp3 = args
    logStart()
    # Calculate retLength
    aLength = nameSym("aLength")
    retLength = nameSym("retLength")
    print(f"var {aLength} 0")
    print(f"var {retLength} 0")
    strlen([retLength, strB, tmp])
    strlen([aLength, strA, tmp])
    add([retLength, aLength, tmp])

    # Allocate ret
    malloc_const([tmp, 24, tmp2])
    setaddr([ret, tmp, tmp2, tmp3])
    mov([tmp, retLength, tmp2])
    mul_8([tmp, tmp2])
    alloc_str([ret, tmp, tmp2])

    # Copy the string content
    strcpy([ret, strA, tmp, tmp2])
    # Hack
    mul_8([aLength, tmp])
    add([ret, aLength, tmp])
    strcpy([ret, strB, tmp, tmp2])
    sub([ret, aLength])

    # Set the string length
    incaddr([ret, 8])
    mov([ret, retLength, tmp])
    decaddr([ret, 8])
    logEnd()


# Does a %= 256
def mod_256(args):
    a, tmp, tmp2 = args
    logStart()
    startLabel = nameSym("START", True)
    endLabel = nameSym("END", True)
    isNegLabel = nameSym("IS_NEG", True)
    checkNegLabel = nameSym("CHECK_NEG", True)
    multSubberStartLabel = nameSym("MULT_SUBBER_START", True)
    subtractALabel = nameSym("SUBTRACT_A", True)
    revertSubLabel = nameSym("REVERT_SUB", True)

    # Negate if a < 0
    isNeg = nameSym("isNeg")
    print(f"var {isNeg} 0")
    zero([isNeg])
    jn([a, isNegLabel, tmp, tmp2])
    lbljmp([startLabel])

    print(f"label {isNegLabel}")
    inc([isNeg, 1])
    neg([a, tmp, tmp2])

    print(f"label {startLabel}")
    subber = nameSym("subber")
    print(f"var {subber} 0")
    inst_set([subber, 0x100])

    # Finish if a < 0x100
    jl([a, subber, checkNegLabel, tmp, tmp2])

    # Multiply subbers by 0x100 until the next multiplication makes subber > a
    nextSubber = nameSym("nextSubber")
    print(f"var {nextSubber} 0")
    inst_set([nextSubber, 0x10000])

    print(f"label {multSubberStartLabel}")
    jl([a, nextSubber, subtractALabel, tmp, tmp2])
    mul_256([subber, tmp])
    mul_256([nextSubber, tmp])
    # nextSubber overflowed
    decleq([nextSubber, 0, subtractALabel])
    lbljmp([multSubberStartLabel])

    # Subtract a by subber until a < 0
    print(f"label {subtractALabel}")
    # Do some unrolling
    for _i in range(8):
        print(f"lblsq {a} {subber} {revertSubLabel}")
    lbljmp([subtractALabel])

    print(f"label {revertSubLabel}")
    jz([a, startLabel, tmp])
    add([a, subber, tmp])
    lbljmp([startLabel])

    print(f"label {checkNegLabel}")
    decleq([isNeg, 0, endLabel])
    # No need to invert if a == 0
    decleq([a, 0, endLabel])
    # a = 256 - a
    mov([tmp, a, tmp2])
    inst_set([a, 0x100])
    sub([a, tmp])

    print(f"label {endLabel}")
    logEnd()


# Halts the system.
def halt(args):
    tmp, tmp2 = args
    logStart()
    # Stop CPU 0
    set_safe(["CPU_CONTROL_START", 2, tmp, tmp2])
    # Infinite loop
    print("relsq ZERO ZERO 0")
    logEnd()


# Converts a small integer into lowercase hex character
# This function assumes that 0 <= a <= 15
def to_nibble(args):
    ret, a, tmp, tmp2 = args
    logStart()
    startLabel = nameSym("START", True)
    charset = nameSym("HEX_CHARSET", True)

    lbljmp([startLabel])
    print(f"label {charset}")
    raw_chars(["0123456789abcdef"])

    print(f"label {startLabel}")
    movneg([tmp, a])
    mul_8([tmp, tmp2])
    print(f"subaddr {charset} {tmp}")

    mov([ret, charset, tmp2])

    # Revert the address
    movneg([tmp2, tmp])
    print(f"subaddr {charset} {tmp2}")
    logEnd()


# Converts integer to string qword
# Handles negative numbers.
def to_qword(args):
    ret, a_orig, a_copy, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    isNegLabel = nameSym("IS_NEG", True)
    subtractALabel = nameSym("SUBTRACT_A", True)
    handleNibbleLabel = nameSym("HANDLE_NIBBLE", True)
    printNibbleLabel = nameSym("PRINT_NIBBLE", True)
    handleLowNibbleLabel = nameSym("HANDLE_LOW_NIBBLE", True)
    endLabel = nameSym("END", True)

    # Allocate ret
    malloc_const([tmp, 24, tmp2])
    setaddr([ret, tmp, tmp2, a_copy])
    alloc_str_const([ret, 16 * 8, tmp2])

    retBuf = nameSym("retBuf")
    print(f"addr {retBuf} 0")
    setaddr([retBuf, ret, tmp, tmp2])

    # Set length
    incaddr([ret, 8])
    inst_set([ret, 16])
    decaddr([ret, 8])

    mov([a_copy, a_orig, tmp])

    # Negate if a < 0
    isNeg = nameSym("isNeg")
    print(f"var {isNeg} 0")
    zero([isNeg])
    jn([a_copy, isNegLabel, tmp, tmp2])
    lbljmp([loopLabel])

    print(f"label {isNegLabel}")
    inc([isNeg, 1])
    neg([a_copy, tmp, tmp2])
    lbljmp([loopLabel])

    subbersLabel = nameSym("SUBBERS", True)
    # The array of subbers is terminated with 0
    subbers = [numToRawInst(0)]
    curSubber = 1
    for _i in range(16):
        subbers.append(numToRawInst(curSubber))
        curSubber *= 16
    print(f"label {subbersLabel}")
    print(f"raw {' '.join(subbers[::-1])}")

    print(f"label {loopLabel}")
    # Finish if the current subber is 0
    jz([subbersLabel, endLabel, tmp])

    nibbleVal = nameSym("nibbleVal")
    print(f"var {nibbleVal} 0")
    zero([nibbleVal])

    # Subtract a by subber until the next subtraction makes a < 0
    print(f"label {subtractALabel}")
    jl([a_copy, subbersLabel, handleNibbleLabel, tmp, tmp2])
    inc([nibbleVal, 1])
    sub([a_copy, subbersLabel])
    lbljmp([subtractALabel])

    print(f"label {handleNibbleLabel}")
    # The least significant nibble and the zeroes that follow it require special treatment
    jz([a_copy, handleLowNibbleLabel, tmp])

    # Handle high nibbles
    decleq([isNeg, 0, printNibbleLabel])
    # nibble = 15 - nibble
    mov([tmp, nibbleVal, tmp2])
    inst_set([nibbleVal, 0xf])
    sub([nibbleVal, tmp])
    lbljmp([printNibbleLabel])

    # Handle low nibbles
    print(f"label {handleLowNibbleLabel}")
    decleq([isNeg, 0, printNibbleLabel])
    # No need to invert a zero nibble
    decleq([nibbleVal, 0, printNibbleLabel])
    # nibble = 16 - nibble
    mov([tmp, nibbleVal, tmp2])
    inst_set([nibbleVal, 0x10])
    sub([nibbleVal, tmp])

    print(f"label {printNibbleLabel}")
    to_nibble([retBuf, nibbleVal, tmp, tmp2])
    incaddr([retBuf, 8])

    incaddr([subbersLabel, 8])
    lbljmp([loopLabel])

    print(f"label {endLabel}")
    decaddr([subbersLabel, 8 * (len(subbers) - 1)])
    logEnd()


# Prints a qword into the serial output in hex format.
# Handles negative numbers.
def print_qword(args):
    a_orig, a_copy, tmp, tmp2, tmp3 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    isNegLabel = nameSym("IS_NEG", True)
    subtractALabel = nameSym("SUBTRACT_A", True)
    handleNibbleLabel = nameSym("HANDLE_NIBBLE", True)
    printNibbleLabel = nameSym("PRINT_NIBBLE", True)
    handleLowNibbleLabel = nameSym("HANDLE_LOW_NIBBLE", True)
    endLabel = nameSym("END", True)

    mov([a_copy, a_orig, tmp])

    # Negate if a < 0
    isNeg = nameSym("isNeg")
    print(f"var {isNeg} 0")
    zero([isNeg])
    jn([a_copy, isNegLabel, tmp, tmp2])
    lbljmp([loopLabel])

    print(f"label {isNegLabel}")
    inc([isNeg, 1])
    neg([a_copy, tmp, tmp2])
    lbljmp([loopLabel])

    subbersLabel = nameSym("SUBBERS", True)
    # The array of subbers is terminated with 0
    subbers = [numToRawInst(0)]
    curSubber = 1
    for _i in range(16):
        subbers.append(numToRawInst(curSubber))
        curSubber *= 16
    print(f"label {subbersLabel}")
    print(f"raw {' '.join(subbers[::-1])}")

    print(f"label {loopLabel}")
    # Finish if the current subber is 0
    jz([subbersLabel, endLabel, tmp])

    nibbleVal = nameSym("nibbleVal")
    print(f"var {nibbleVal} 0")
    zero([nibbleVal])

    # Subtract a by subber until the next subtraction makes a < 0
    print(f"label {subtractALabel}")
    jl([a_copy, subbersLabel, handleNibbleLabel, tmp, tmp2])
    inc([nibbleVal, 1])
    sub([a_copy, subbersLabel])
    lbljmp([subtractALabel])

    print(f"label {handleNibbleLabel}")
    # The least significant nibble and the zeroes that follow it require special treatment
    jz([a_copy, handleLowNibbleLabel, tmp])

    # Handle high nibbles
    decleq([isNeg, 0, printNibbleLabel])
    # nibble = 15 - nibble
    mov([tmp, nibbleVal, tmp2])
    inst_set([nibbleVal, 0xf])
    sub([nibbleVal, tmp])
    lbljmp([printNibbleLabel])

    # Handle low nibbles
    print(f"label {handleLowNibbleLabel}")
    decleq([isNeg, 0, printNibbleLabel])
    # No need to invert a zero nibble
    decleq([nibbleVal, 0, printNibbleLabel])
    # nibble = 16 - nibble
    mov([tmp, nibbleVal, tmp2])
    inst_set([nibbleVal, 0x10])
    sub([nibbleVal, tmp])

    print(f"label {printNibbleLabel}")
    to_nibble([tmp, nibbleVal, tmp2, tmp3])
    putchar([tmp, tmp2])

    incaddr([subbersLabel, 8])
    lbljmp([loopLabel])

    print(f"label {endLabel}")
    decaddr([subbersLabel, 8 * (len(subbers) - 1)])
    logEnd()


# Converts integer to string in base 10
# Handles negative numbers.
def itoa(args):
    ret, a_orig, a_copy, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    isNegLabel = nameSym("IS_NEG", True)
    isZeroLabel = nameSym("IS_ZERO", True)
    subtractALabel = nameSym("SUBTRACT_A", True)
    handleDigitLabel = nameSym("HANDLE_DIGIT", True)
    printDigitLabel = nameSym("PRINT_DIGIT", True)
    dontPrintDigitLabel = nameSym("DONT_PRINT_DIGIT", True)
    revertSubbersSymbol = nameSym("REVERT_SUBBERS", True)
    endLabel = nameSym("END", True)

    # Allocate ret
    malloc_const([tmp, 24, tmp2])
    setaddr([ret, tmp, tmp2, a_copy])
    alloc_str_const([ret, 20 * 8, tmp2])

    retBuf = nameSym("retBuf")
    print(f"addr {retBuf} 0")
    setaddr([retBuf, ret, tmp, tmp2])

    retLength = nameSym("retLength")
    print(f"addr {retLength} 0")
    copyaddr([retLength, ret, tmp, tmp2])
    incaddr([retLength, 8])

    noDigits = nameSym("noDigits")
    print(f"var {noDigits} 0")
    inst_set([noDigits, 1])

    mov([a_copy, a_orig, tmp])

    # Negate if a < 0
    isNeg = nameSym("isNeg")
    print(f"var {isNeg} 0")
    zero([isNeg])
    jn([a_copy, isNegLabel, tmp, tmp2])

    # Handle a = 0
    jz([a_copy, isZeroLabel, tmp])
    lbljmp([loopLabel])

    print(f"label {isZeroLabel}")
    # Append 0 to the string
    inst_set([retBuf, ord("0")])
    inc([retLength, 1])
    lbljmp([endLabel])

    print(f"label {isNegLabel}")
    inc([isNeg, 1])
    neg([a_copy, tmp, tmp2])
    # Append - to the string
    inst_set([retBuf, ord("-")])
    incaddr([retBuf, 8])
    inc([retLength, 1])
    lbljmp([loopLabel])

    subbersLabel = nameSym("SUBBERS", True)
    # The array of subbers is terminated with 0
    subbers = [numToRawInst(0)]
    curSubber = 1
    for _i in range(19):
        subbers.append(numToRawInst(curSubber))
        curSubber *= 10
    print(f"label {subbersLabel}")
    print(f"raw {' '.join(subbers[::-1])}")

    print(f"label {loopLabel}")
    # Finish if the current subber is 0
    jz([subbersLabel, revertSubbersSymbol, tmp])

    digitVal = nameSym("digitVal")
    print(f"var {digitVal} 0")
    zero([digitVal])

    # Subtract a by subber until the next subtraction makes a < 0
    print(f"label {subtractALabel}")
    jl([a_copy, subbersLabel, handleDigitLabel, tmp, tmp2])
    inc([digitVal, 1])
    sub([a_copy, subbersLabel])
    lbljmp([subtractALabel])

    print(f"label {handleDigitLabel}")
    # Don't print zero digits before non-zero digits
    jz([noDigits, printDigitLabel, tmp])
    jz([digitVal, dontPrintDigitLabel, tmp])

    print(f"label {printDigitLabel}")
    zero([noDigits])
    inst_set([retBuf, ord("0")])
    add([retBuf, digitVal, tmp])
    incaddr([retBuf, 8])
    inc([retLength, 1])

    print(f"label {dontPrintDigitLabel}")
    incaddr([subbersLabel, 8])
    lbljmp([loopLabel])

    print(f"label {revertSubbersSymbol}")
    decaddr([subbersLabel, 8 * (len(subbers) - 1)])
    print(f"label {endLabel}")
    logEnd()


# Converts a hex string to integer value and stores the value in a
# Handles negative sign (-)
# Half of the codes here are pretty much copied from hex1_monitor.
def from_hex(args):
    orgA, string, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    negSignLabel = nameSym("NEG_SIGN", True)
    writeLabel = nameSym("WRITE", True)
    negateLabel = nameSym("NEGATE", True)
    endLabel = nameSym("END", True)

    a = nameSym("a")
    print(f"addr {a} 0")
    copyaddr([a, orgA, tmp, tmp2])
    zero([a])

    strBuf = nameSym("strBuf")
    print(f"addr {strBuf} 0")
    setaddr([strBuf, string, tmp, tmp2])

    strLen = nameSym("strLen")
    print(f"var {strLen} 0")
    incaddr([string, 8])
    mov([strLen, string, tmp])
    decaddr([string, 8])

    # Handle sign (-)
    isNeg = nameSym("isNeg")
    print(f"var {isNeg} 0")
    zero([isNeg])

    mov([tmp, strBuf, tmp2])
    # Handle NUL ~ ,
    decleq([tmp, 0x2c, loopLabel])
    # Handle -
    decleq([tmp, 0x1, negSignLabel])
    lbljmp([loopLabel])

    print(f"label {negSignLabel}")
    inc([isNeg, 1])
    dec([strLen, 1])
    incaddr([strBuf, 8])

    print(f"label {loopLabel}")
    decleq([strLen, 0, negateLabel])
    dec([strLen, 1])
    mov([tmp, strBuf, tmp2])
    incaddr([strBuf, 8])

    val = nameSym("val")
    print(f"var {val} 0")
    zero([val])

    # Handle 0 ~ 9
    dec([tmp, 0x2f])
    movneg([val, tmp])
    inc([val, 1])
    decleq([tmp, 0xa, writeLabel])

    # Handle A ~ F
    dec([tmp, 0x7])
    movneg([val, tmp])
    dec([val, 0x9])
    decleq([tmp, 0x6, writeLabel])

    # Handle a ~ f
    dec([tmp, 0x1a])
    movneg([val, tmp])
    dec([val, 0x9])

    print(f"label {writeLabel}")
    mul_16([a, tmp])
    sub([a, val])
    lbljmp([loopLabel])

    print(f"label {negateLabel}")
    decleq([isNeg, 0, endLabel])
    neg([a, tmp, tmp2])

    print(f"label {endLabel}")
    logEnd()


# An array is made out of four parts:
# 1. Address to the array's buffer
# 2. Number of elements in the array
# 3. The size of every element in the array
# 4. The capacity of the buffer

# Goes through a buffer of items until it finds an item that matches the wanted key
# When there is a match, it will jump to foundLabel with "it"'s address pointing to the matched item
# When there isn't a match, it doesn't jump and makes "it"'s address point right after the last element
# The first component of the items must be a string that contains the key
# "it" is the shorthand for the iterator, like the one in C++
def find_item_in_buf_with_str_key(args):
    it, key, elmSize, elmCount, foundLabel, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    noMatchLabel = nameSym("NO_MATCH", True)

    elmsLeft = nameSym("elmsLeft")
    print(f"var {elmsLeft} 0")
    mov([elmsLeft, elmCount, tmp])

    print(f"label {loopLabel}")
    decleq([elmsLeft, 0, noMatchLabel])
    dec([elmsLeft, 1])
    strcmp_const([it, key, foundLabel, tmp, tmp2])
    incaddr([it, elmSize])
    lbljmp([loopLabel])

    print(f"label {noMatchLabel}")
    logEnd()


# Same as memcpy, except num is a constant
def memcpy_const(args):
    orgDst, orgSrc, num, tmp, tmp2 = args
    logStart()
    memcpy([orgDst, orgSrc, recordConst(num), tmp, tmp2])
    logEnd()


# Copies num bytes of data from src to dst
# Currently only supports len % 8 == 0
def memcpy(args):
    orgDst, orgSrc, num, tmp, tmp2 = args
    logStart()
    loopLabel = nameSym("LOOP", True)
    endLabel = nameSym("END", True)

    dst = nameSym("dst")
    src = nameSym("src")
    print(f"addr {dst} 0")
    print(f"addr {src} 0")
    copyaddr([dst, orgDst, tmp, tmp2])
    copyaddr([src, orgSrc, tmp, tmp2])

    numLeft = nameSym("numLeft")
    print(f"var {numLeft} 0")
    mov([numLeft, num, tmp])

    print(f"label {loopLabel}")
    decleq([numLeft, 0, endLabel])
    dec([numLeft, 8])
    mov([dst, src, tmp])
    incaddr([dst, 8])
    incaddr([src, 8])
    lbljmp([loopLabel])

    print(f"label {endLabel}")
    logEnd()


subroutineCallCounts = {}


# Helper for calling a subroutine
def call(args):
    name, tmp = args
    logStart()
    if name not in subroutineCallCounts:
        subroutineCallCounts[name] = 0
    callId = subroutineCallCounts[name]
    retPos = f"{name}_retPos_{callId}"
    retPosAddr = f"{name}_retPosAddr_{callId}"
    subroutineCallCounts[name] += 1

    mov([f"{name}_retAddr", retPosAddr, tmp])
    lbljmp([name])
    print(f"label {retPosAddr}")
    print(f"raw_ref {retPos}")
    print(f"label {retPos}")
    logEnd()


# Helper for having a subroutine return to its caller
def ret(args):
    assert len(args) == 1
    name = args[0]
    logStart()
    print(f"raw {numToRawInst(0)} {numToRawInst(0)}")
    print(f"label {name}_retAddr")
    print(f"raw {numToRawInst(0)}")
    logEnd()


parser = argparse.ArgumentParser(prog="msq_to_lsq", description="Translates a msq_to_lsq program into lsq code")
parser.add_argument("msq_path", help="Path to the msq file")
parser.add_argument("--verbosity", dest="verbosity", metavar="N", type=int, default=3, help="How deep the MSQ_START and MSQ_END prints should get (default is 3)")
args = parser.parse_args()
verbosity = args.verbosity

lines = open(sys.argv[1]).read().split("\n")
print("0", end="")
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
