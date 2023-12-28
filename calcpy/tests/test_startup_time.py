#!/usr/bin/env python3

import subprocess
import time

def test_startup_time(n=10):
    # warmup:
    subprocess.check_call(['calcpy', '-c', '4+4'], stdout=None, stdin=subprocess.PIPE)

    elapsed = []
    for i in range(n):
        start_time = time.time()
        subprocess.check_call(['calcpy', '-c', '4+4'], stdout=None, stdin=subprocess.PIPE)
        elapsed.append(time.time() - start_time)
        print(elapsed[-1])
    print(f'max {max(elapsed)}')
    print(f'min {min(elapsed)}')
    print(f'avg {sum(elapsed)/n}')

if __name__ == "__main__":
    test_startup_time()
