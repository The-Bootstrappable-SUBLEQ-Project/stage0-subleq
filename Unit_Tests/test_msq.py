#!/usr/bin/python3
from .utils import runEmu


def test_msq_jeq():
    assert runEmu("../Examples/test_jeq", []) == b".\n"


def test_msq_str():
    assert runEmu("../Examples/test_str", []) == b".\n"
