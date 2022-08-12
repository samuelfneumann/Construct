from construct_py.construct_py import parse
import pytest
import numpy as np
import torch
import tomli


# Tests to see if the net.toml file is constructed properly
def test_net():
    with open("example_configs/net.toml", "rb") as infile:
        config = tomli.load(infile)

    out = parse(config)
    assert isinstance(out, torch.nn.Sequential), "not a torch.nn.Sequential"
    assert isinstance(out[0], torch.nn.Conv2d), "not a torch.nn.Conv2d"
    assert isinstance(out[1], torch.nn.ReLU), "not a torch.nn.ReLU"
    assert isinstance(out[2], torch.nn.Flatten), "not a torch.nn.Flatten"
    assert isinstance(out[3], torch.nn.Linear), "not a torch.nn.Linear"
    assert isinstance(out[4], torch.nn.ReLU), "not a torch.nn.ReLU"
    assert isinstance(out[5], torch.nn.Linear), "not a torch.nn.Linear"


# Tests to see if the rng.toml file is constructed properly
def test_rng():
    with open("example_configs/rng.toml", "rb") as infile:
        config = tomli.load(infile)

    out = parse(config)
    assert isinstance(out, np.random.Generator), "not a np.random.Generator"
