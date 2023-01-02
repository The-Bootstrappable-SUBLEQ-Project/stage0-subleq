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

# Well...now I have to worry about these
lsq_insts = ["var", "label", "addr",
             "abssq", "relsq", "lblsq",
             "subaddr", "zeroaddr",
             "raw", "rem"]

# Entry format: [Inst, Tokens, Comment]
lines = []

# TODO: Take hex_version as a parameter
hex_version = 0
# Only hex0 is supported currently
assert hex_version == 0

inp = open(sys.argv[1]).read().split("\n")
for line in inp:
    if len(line.strip()) == 0:
        lines.append(["newline", [], ""])
        continue

    tokens = line.split()
    if tokens[0] == "rem":
        lines.append(["rem", [], " ".join(tokens[1:])])
        continue
    elif tokens[0] in lsq_insts:
        lines.append([tokens[0], tokens[1:], ""])
    else:
        raise SyntaxError(f"Unknown instruction: {tokens[0]}")

# Entry format: [Address, RefCount, References (LineNum, TokenId)]
symbols = {}
for line in lines:
    if line[0] in ["var", "label", "addr"]:
        symbols[line[1][0]] = [int(line[1][1], 16) if line[0] == "addr" else None, 0, []]

# Count references
for line in lines:
    if line[0] in ["abssq", "relsq", "lblsq"]:
        symbols[line[1][0]][1] += 1
        symbols[line[1][1]][1] += 1
        if line[0] == "lblsq":
            symbols[line[1][2]][1] += 1
    elif line[0] == "subaddr":
        symbols[line[1][1]][1] += 1
print(symbols)

i = 0
while i < len(lines):
    if lines[i][0] not in ["subaddr", "zeroaddr"]:
        i += 1
        continue
    sym = lines[i][1][0]
    if lines[i][0] == "subaddr":
        lines[i:i+1] = [f"relsq {sym}_decaddr_{x} {lines[i][1][1]} 1"]
    i += 1
    pass