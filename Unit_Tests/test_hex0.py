#!/usr/bin/python3
from .utils import runEmu


def test_hex0_hello_world():
    assert runEmu("../phase0-hex/hex0", ["../Examples/hello_world.hex0"], 30) == open("../Examples/hello_world.bin", "rb").read()
