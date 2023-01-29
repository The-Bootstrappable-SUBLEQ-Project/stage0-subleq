#!/usr/bin/python3
from .utils import runEmu
import pytest


def test_hex1_monitor_load():
    assert runEmu("../phase0-hex/hex1_monitor", ["../Examples/hello_world.hex1"], 10) == b"Hello, World!\n"


def test_hex1_monitor_load_one_pass():
    assert runEmu("../phase0-hex/hex1_monitor", ["../phase0-hex/hex1_monitor.hex1", "../Examples/hello_world.hex1"], 10) == b"Hello, World!\n"


def test_hex1_monitor_load_two_pass():
    assert runEmu("../phase0-hex/hex1_monitor",
                  ["../phase0-hex/hex1_monitor.hex1"] * 2 + ["../Examples/hello_world.hex1"],
                  10) == b"Hello, World!\n"


@pytest.mark.slow
def test_hex1_monitor_load_ten_pass():
    assert runEmu("../phase0-hex/hex1_monitor",
                  ["../phase0-hex/hex1_monitor.hex1"] * 10 + ["../Examples/hello_world.hex1"],
                  30) == b"Hello, World!\n"


def test_hex1_monitor_bootstrap():
    assert runEmu("../phase0-hex/hex0_monitor",
                  ["../phase0-hex/hex0_monitor.hex0", "../phase0-hex/hex0_monitor.hex0",
                   "../phase0-hex/hex1_monitor.hex0", "../phase0-hex/hex1_monitor.hex1", "../phase0-hex/hex1_monitor.hex1",
                   "../Examples/hello_world.hex1"], 10) == b"Hello, World!\n"
