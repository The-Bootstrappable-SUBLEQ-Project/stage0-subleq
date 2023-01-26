#!/usr/bin/python3
from .utils import runEmu
import pytest


def test_hex0_monitor_load():
    assert runEmu("../phase0-hex/hex0_monitor", ["../Examples/hello_world.hex0"], 10) == b"Hello, World!\n"


def test_hex0_monitor_load_one_pass():
    assert runEmu("../phase0-hex/hex0_monitor", ["../phase0-hex/hex0_monitor.hex0", "../Examples/hello_world.hex0"], 10) == b"Hello, World!\n"


def test_hex0_monitor_load_two_pass():
    assert runEmu("../phase0-hex/hex0_monitor",
                  ["../phase0-hex/hex0_monitor.hex0"] * 2 + ["../Examples/hello_world.hex0"],
                  10) == b"Hello, World!\n"


@pytest.mark.slow
def test_hex0_monitor_load_ten_pass():
    assert runEmu("../phase0-hex/hex0_monitor",
                  ["../phase0-hex/hex0_monitor.hex0"] * 10 + ["../Examples/hello_world.hex0"],
                  30) == b"Hello, World!\n"
