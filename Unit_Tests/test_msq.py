#!/usr/bin/python3
from .utils import runEmu


def test_msq_jeq():
    assert runEmu("../Examples/test_jeq", []) == b".\n"


def test_msq_str():
    assert runEmu("../Examples/test_str", []) == b".\n"


def test_msq_print_qword():
    assert runEmu("../Examples/test_print_qword", []) == b"0000000000000000 ffffffffffffffff 0123456789abcdef fedcba9876543210 f123456789abcdef\n"
