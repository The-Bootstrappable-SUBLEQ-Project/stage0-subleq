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
# https://stackoverflow.com/a/62775680
from __future__ import annotations
import sys
from dataclasses import dataclass, field
import pprint
import struct
import string
import itertools
import argparse

pp = pprint.PrettyPrinter()

# Well...now I have to worry about these
lsq_insts = ["var", "label", "addr",
             "abssq", "relsq", "lblsq",
             "subaddr", "zeroaddr",
             "raw", "raw_ref", "rem"]


@dataclass
class Line:
    inst: str
    # https://stackoverflow.com/a/74292633
    tokens: list[str] = field(default_factory=list)
    comment: str = ""
    offset: int = 0


@dataclass
class Reference:
    lineNum: int
    tokenId: int


@dataclass
class Symbol:
    addr: int = None
    refCount: int = 0
    val: int = None


def toLong(inp):
    return struct.pack(">q", inp).hex().ljust(16, "0")


parser = argparse.ArgumentParser(prog="lsq_to_hex", description="Assembles a lsq program into hex0~hex2 codes")
parser.add_argument("lsq_path", help="Path to the lsq file")
parser.add_argument("--hex-version", dest="hex_version", metavar="N", type=int, default=0, help="The hex version to output (0~2, default is 0)")
args = parser.parse_args()

hex_version = args.hex_version
assert hex_version in [0, 1, 2]

# 0. Parse file into lines
lines = []
inp = open(args.lsq_path).read().split("\n")
for line in inp:
    if len(line.strip()) == 0:
        lines.append(Line("newline"))
        continue

    tokens = line.split()
    inst = tokens[0]
    if inst == "rem":
        lines.append(Line("rem", [], " ".join(tokens[1:])))
        continue
    elif inst in lsq_insts:
        lines.append(Line(inst, tokens[1:]))
    else:
        raise SyntaxError(f"Unknown instruction: {inst}")

# 1. Find symbols
symbols = {}
for line in lines:
    if line.inst in ["var", "label", "addr"]:
        symbols[line.tokens[0]] = Symbol(int(line.tokens[1], 16) if line.inst == "addr" else None)
        if line.inst == "var":
            symbols[line.tokens[0]].val = int(line.tokens[1], 16)

# 2. Count symbol references (Pass 1)
for line in lines:
    if line.inst in ["abssq", "relsq", "lblsq"]:
        symbols[line.tokens[0]].refCount += 1
        symbols[line.tokens[1]].refCount += 1
        if line.inst == "lblsq":
            symbols[line.tokens[2]].refCount += 1
    elif line.inst == "subaddr":
        symbols[line.tokens[1]].refCount += 1
    elif line.inst == "raw_ref":
        for token in line.tokens:
            symbols[token].refCount += 1

# 3. Create subaddr/zeroaddr stubs
i = 0
# Format: {SymbolName: NextId}
addrSymbols = {}
while i < len(lines):
    if lines[i].inst not in ["subaddr", "zeroaddr"]:
        i += 1
        continue
    sym = lines[i].tokens[0]
    addrSymbols[sym] = 0

    stubSym = f"{sym}_addrRef_"

    if lines[i].inst == "subaddr":
        lines[i:i + 1] = [Line("relsq", [f"{stubSym}{x}", lines[i].tokens[1], "1"]) for x in range(symbols[sym].refCount)]
    elif lines[i].inst == "zeroaddr":
        lines[i:i + 1] = [Line("relsq", [f"{stubSym}{x}", f"{stubSym}{x}", "1"]) for x in range(symbols[sym].refCount)]

    for k in range(symbols[sym].refCount):
        curSym = f"{stubSym}{k}"
        if curSym in symbols:
            symbols[curSym].refCount += 1
        else:
            symbols[curSym] = Symbol(None, 1)
    i += 1

# 4. Find label+stub addresses and convert relsq to abssq on hex0
size = 0
for line in lines:
    line.offset = size
    if line.inst in ["abssq", "relsq", "lblsq"]:
        for i in range(3):
            sym = line.tokens[i]
            if (line.inst == "lblsq" or i < 2) and sym in addrSymbols:
                stubSym = f"{sym}_addrRef_{addrSymbols[sym]}"
                symbols[stubSym].addr = size
                addrSymbols[sym] += 1
            size += 8
    elif line.inst == "raw":
        size += 8 * len(line.tokens)
    elif line.inst == "raw_ref":
        size += 8 * len(line.tokens)
    elif line.inst == "label":
        symbols[line.tokens[0]].addr = size
    # print(line, size, file=sys.stderr)

# 5. Assign addresses to variables
symsAtAddr = {}
for name, sym in symbols.items():
    if sym.addr is None:
        assert sym.val is not None
        sym.addr = size
        lines.append(Line("raw", [toLong(sym.val)], name))
        size += 8

    if sym.addr not in symsAtAddr:
        symsAtAddr[sym.addr] = []
    symsAtAddr[sym.addr].append(name)

# 6. Output
"""
lsq_insts = ["var", "label", "addr",
             "abssq", "relsq", "lblsq",
             "subaddr", "zeroaddr",
             "raw", "raw_ref", "rem"]
"""

out = []
offset = 0
availShortNames = ["".join(p) for p in itertools.product(string.ascii_letters, repeat=2)]
shortNames = {}


def addToken(token):
    global offset
    if offset in symsAtAddr:
        for name in symsAtAddr[offset]:
            if hex_version == 1:
                if name not in shortNames:
                    shortNames[name] = availShortNames.pop(0)
                out.append(f":{shortNames[name]}")
            elif hex_version == 2:
                out.append(f":{name}")
    out.append(token)
    offset += 8


def resolveSymbol(name):
    addr = symbols[name].addr
    if hex_version == 0 or addr >= size:
        return toLong(addr)
    elif hex_version == 1:
        if name not in shortNames:
            shortNames[name] = availShortNames.pop(0)
        return f"&{shortNames[name]}"
    else:
        return f"&{name}"


print(f"# hex{hex_version}")

for line in lines:
    out = []
    if line.inst in ["var", "label", "addr", "rem", "newline"]:
        pass
    elif line.inst in ["abssq", "relsq", "lblsq"]:
        addToken(resolveSymbol(line.tokens[0]))
        addToken(resolveSymbol(line.tokens[1]))
        if line.inst == "abssq":
            addToken(toLong(int(line.tokens[2], 16)))
        elif line.inst == "relsq":
            target = line.offset + 24 * (int(line.tokens[2], 16))
            if hex_version == 0:
                addToken(toLong(target))
            else:
                diff = target - offset
                addToken(f"?{diff:+x}")
        elif line.inst == "lblsq":
            addToken(resolveSymbol(line.tokens[2]))
    elif line.inst == "raw":
        for token in line.tokens:
            addToken(token)
    elif line.inst == "raw_ref":
        for token in line.tokens:
            addToken(resolveSymbol(token))
    else:
        raise RuntimeError(f"Instruction {line.inst} shouldn't have appeared at this step!")

    if line.inst not in ["rem", "newline"]:
        out.append(f"; {line.inst} {' '.join(line.tokens)}")
    if len(line.comment) != 0:
        out.append(f"# {line.comment}")

    print(" ".join(out))

# ~ is the terminator of hex files
print("~")

print(f"Binary size of {args.lsq_path}: {size} (0x{size:x}) bytes", file=sys.stderr)
