#!/usr/bin/python3
from .utils import runEmu
import pytest
import glob


def test_hex2_hello_world():
    assert runEmu("../phase0-hex/hex2", ["../Examples/hello_world.hex2"], 30) == open("../Examples/hello_world.bin", "rb").read()


def test_hex2_hex2_monitor():
    assert runEmu("../phase0-hex/hex2", ["../phase0-hex/hex2_monitor.hex2"], 30) == open("../phase0-hex/hex2_monitor.bin", "rb").read()


def test_hex2_hex2():
    assert runEmu("../phase0-hex/hex2", ["../phase0-hex/hex2.hex2"], 30) == open("../phase0-hex/hex2.bin", "rb").read()


@pytest.mark.slow
def test_hex2_everything_else():
    alreadyTested = ["../Examples/hello_world.hex2", "../phase0-hex/hex2_monitor.hex2", "../phase0-hex/hex2.hex2"]
    hex2Files = glob.glob("../**/*.hex2")
    for path in hex2Files:
        if path in alreadyTested:
            continue
        basePath = path[:-5]
        print("Confirming", basePath)
        assert runEmu("../phase0-hex/hex2", [basePath + ".hex2"], 300) == open(basePath + ".bin", "rb").read()
