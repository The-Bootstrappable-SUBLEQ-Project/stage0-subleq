#!/usr/bin/python3
from .utils import runEmu
import pytest
import tqdm


def test_hello_world():
    assert runEmu("../Examples/hello_world") == b"Hello, World!\n"


def test_hello_world_repeat_100():
    for _i in tqdm.trange(100):
        test_hello_world()


@pytest.mark.slow
def test_hello_world_repeat_1000():
    for _i in tqdm.trange(1000):
        test_hello_world()


@pytest.mark.slower
def test_hello_world_repeat_10000():
    for _i in tqdm.trange(10000):
        test_hello_world()
