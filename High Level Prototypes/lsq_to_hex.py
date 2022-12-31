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
             "decaddr", "setaddr",
             "raw", "rem"]
lines = []

inp = open(sys.argv[1]).read().split("\n")
for line in inp:
    if len(line.strip()) == 0:
        lines.append(("newline", [], ""))
        continue

    tokens = line.split()
    if tokens[0] == "rem":
        lines.append(("rem", [], " ".join(tokens[1:])))
        continue
    elif tokens[0] in lsq_insts:
        lines.append((tokens[0], tokens[1:], ""))
    else:
        raise SyntaxError(f"Unknown instruction: {tokens[0]}")

print(lines)
