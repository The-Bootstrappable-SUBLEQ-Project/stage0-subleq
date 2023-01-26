#!/usr/bin/python3
from .utils import runEmu


def test_hex0_hello_world():
    assert runEmu("../phase0-hex/hex0", ["../Examples/hello_world.hex0"], 30) == open("../Examples/hello_world.bin", "rb").read()


def test_hex0_hex0_monitor():
    assert runEmu("../phase0-hex/hex0", ["../phase0-hex/hex0_monitor.hex0"], 30) == open("../phase0-hex/hex0_monitor.bin", "rb").read()


def test_hex0_hex0():
    assert runEmu("../phase0-hex/hex0", ["../phase0-hex/hex0.hex0"], 30) == open("../phase0-hex/hex0.bin", "rb").read()
