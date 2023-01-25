#!/usr/bin/python3
from .utils import runEmu


def test_hello_world():
    assert runEmu("../Examples/hello_world") == b"Hello, World!\n"

def test_hello_world_repeat_100():
    for i in range(100):
        print(i)
        test_hello_world()

def test_hello_world_repeat_1000():
    for i in range(1000):
        print(i)
        test_hello_world()