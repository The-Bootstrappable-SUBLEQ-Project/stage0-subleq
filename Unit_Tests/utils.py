#!/usr/bin/python3
import subprocess
import string
import random
import os


def getTempFilePath():
    return "/tmp/stage0_subleq_test_batch_input_" + ''.join(random.choice(string.ascii_letters) for i in range(20))


def runEmu(base_path, inps=None, timeout=3):
    tempFilePath = None
    if inps is None or len(inps) == 0:
        # Feed some random file
        batch_input = "../LICENSE"
    elif len(inps) == 1:
        batch_input = inps[0]
    else:
        tempFilePath = getTempFilePath()
        with open(tempFilePath, "wb") as tempFile:
            for path in inps:
                with open(path, "rb") as f:
                    tempFile.write(f.read())
        batch_input = tempFilePath

    try:
        ret = subprocess.check_output(["../../noontide-emu/target/release/noontide-emu", "-b", batch_input, base_path], timeout=timeout)
    except Exception:
        ret = f"Error: Timeout after {timeout}s"
    finally:
        if tempFilePath is not None:
            os.remove(tempFilePath)

    return ret
