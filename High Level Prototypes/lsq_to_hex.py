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
from dataclasses import dataclass

# Well...now I have to worry about these
lsq_insts = ["var", "label", "addr",
             "abssq", "relsq", "lblsq",
             "subaddr", "zeroaddr",
             "raw", "rem"]


@dataclass
class Line:
    inst: str
    tokens: list[str]
    comment: str = ""


@dataclass
class Reference:
    lineNum: int
    tokenId: int


@dataclass
class Symbol:
    addr: int
    refCount: int = 0
    refs: list[Reference] = []


# TODO: Take hex_version as a parameter
hex_version = 0
# Only hex0 is supported currently
assert hex_version == 0

lines = []
inp = open(sys.argv[1]).read().split("\n")
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
        lines.append(line(inst, tokens[1:]))
    else:
        raise SyntaxError(f"Unknown instruction: {inst}")

# Entry format: [Address, RefCount, References (LineNum, TokenId)]
symbols = {}
for line in lines:
    if line[0] in ["var", "label", "addr"]:
        symbols[line.tokens[0]] = Symbol(int(line[1][1], 16) if line[0] == "addr" else None)

# Count references
for line in lines:
    if line[0] in ["abssq", "relsq", "lblsq"]:
        symbols[line.tokens[0]].refCount += 1
        symbols[line.tokens[1]].refCount += 1
        if line[0] == "lblsq":
            symbols[line.tokens[2]].refCount += 1
    elif line[0] == "subaddr":
        symbols[line.tokens[1]].refCount += 1
print(symbols)

i = 0
while i < len(lines):
    if lines[i].inst not in ["subaddr", "zeroaddr"]:
        i += 1
        continue
    sym = lines[i].tokens[0]
    if lines[i].inst == "subaddr":
        lines[i:i + 1] = [Line("relsq", [f"{sym}_subaddr_{x}", f"{lines[i][1][1]}", "1"]) for x in range(symbols[sym].refCount)]
    i += 1
    pass
print(lines)
