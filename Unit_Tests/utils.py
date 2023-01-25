#!/usr/bin/python3
import subprocess

tempFilePath = "/tmp/stage0_subleq_test_batch_input"


def runEmu(base_path, inps=None, timeout=1):
    if inps is None or len(inps) == 0:
        # Feed some random file
        batch_input = "../LICENSE"
    elif len(inps) == 1:
        batch_input = inps[0]
    else:
        with open(tempFilePath, "wb") as tempFile:
            for path in inps:
                with open(path, "rb") as f:
                    tempFile.write(f.read())
        batch_input = tempFilePath

    return subprocess.check_output(["../../noontide-emu/target/release/noontide-emu", "-b", batch_input, base_path], timeout=timeout)
