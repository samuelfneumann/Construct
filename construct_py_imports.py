def test_fn(x, _):
    import numpy as np
    import time
    newRNG = np.random.default_rng(int(time.time()))
    x.bit_generator.state = newRNG.bit_generator.state


def add(*args):
    return sum(*args)


def identity(x):
    return x
