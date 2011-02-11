# compatibility layer for CPython's random module

import System.Random

R = System.Random()

def random():
    """Return a random number in the range [0, 1)"""
    return R.NextDouble()

def choice(seq):
    """Return a random element of a given sequence"""
    i = int(random() * len(seq))
    return seq[i]

