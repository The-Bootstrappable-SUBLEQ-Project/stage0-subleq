#!/usr/bin/python3
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--runslower", action="store_true", default=False, help="run slower tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line(
        "markers", "slower: mark test as extremely slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslower"):
        # --runslower given in cli: do not skip slower tests
        return
    skip_slower = pytest.mark.skip(reason="need --runslower option to run")
    for item in items:
        if "slower" in item.keywords:
            item.add_marker(skip_slower)

    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)
