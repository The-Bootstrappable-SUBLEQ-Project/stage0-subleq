#!/usr/bin/python3
from .utils import runEmu
import pytest
import glob


def test_hex1_hello_world():
    assert runEmu("../phase0-hex/hex1", ["../Examples/hello_world.hex1"], 30) == open("../Examples/hello_world.bin", "rb").read()


def test_hex1_hex1_monitor():
    assert runEmu("../phase0-hex/hex1", ["../phase0-hex/hex1_monitor.hex1"], 30) == open("../phase0-hex/hex1_monitor.bin", "rb").read()


def test_hex1_hex1():
    assert runEmu("../phase0-hex/hex1", ["../phase0-hex/hex1.hex1"], 30) == open("../phase0-hex/hex1.bin", "rb").read()


@pytest.mark.slow
def test_hex1_everything_else():
    alreadyTested = ["../Examples/hello_world.hex1", "../phase0-hex/hex1_monitor.hex1", "../phase0-hex/hex1.hex1"]
    hex1Files = glob.glob("../**/*.hex1")
    for path in hex1Files:
        if path in alreadyTested:
            continue
        basePath = path[:-5]
        print("Confirming", basePath)
        assert runEmu("../phase0-hex/hex1", [basePath + ".hex1"], 300) == open(basePath + ".bin", "rb").read()
