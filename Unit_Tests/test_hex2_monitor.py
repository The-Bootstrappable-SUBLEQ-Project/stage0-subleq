#!/usr/bin/python3
from .utils import runEmu
import pytest


def test_hex2_monitor_load():
    assert runEmu("../phase0-hex/hex2_monitor", ["../Examples/hello_world.hex2"], 10) == b"Hello, World!\n"


def test_hex2_monitor_load_one_pass():
    assert runEmu("../phase0-hex/hex2_monitor", ["../phase0-hex/hex2_monitor.hex2", "../Examples/hello_world.hex2"], 10) == b"Hello, World!\n"


def test_hex2_monitor_load_two_pass():
    assert runEmu("../phase0-hex/hex2_monitor",
                  ["../phase0-hex/hex2_monitor.hex2"] * 2 + ["../Examples/hello_world.hex2"],
                  10) == b"Hello, World!\n"


@pytest.mark.slow
def test_hex2_monitor_load_ten_pass():
    assert runEmu("../phase0-hex/hex2_monitor",
                  ["../phase0-hex/hex2_monitor.hex2"] * 10 + ["../Examples/hello_world.hex2"],
                  30) == b"Hello, World!\n"


def test_hex2_monitor_bootstrap():
    assert runEmu("../phase0-hex/hex0_monitor",
                  ["../phase0-hex/hex0_monitor.hex0", "../phase0-hex/hex0_monitor.hex0",
                   "../phase0-hex/hex1_monitor.hex0", "../phase0-hex/hex1_monitor.hex1", "../phase0-hex/hex1_monitor.hex1",
                   "../phase0-hex/hex2_monitor.hex1", "../phase0-hex/hex2_monitor.hex2", "../phase0-hex/hex2_monitor.hex2",
                   "../Examples/hello_world.hex2"], 30) == b"Hello, World!\n"
