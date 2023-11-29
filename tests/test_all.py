import subprocess

from pathlib import Path

import pytest

from seqsum import lib

data_dir = Path("tests/data")


def run(cmd, cwd=data_dir):  # Helper for CLI testing
    return subprocess.run(
        cmd, cwd=cwd, shell=True, check=True, text=True, capture_output=True
    )


def test_cli_version():
    run("seqsum --version")


def test_cli_sars2_tsv():
    run("seqsum nt MN908947.fasta")
    run("seqsum nt MN908947.fasta --json")


def test_sars2_xxh128():
    assert lib.sum_nt("tests/data/MN908947.fasta") == (
        {"MN908947.3": "ca5e95436b957f93"},
        None,
    )


def test_normlise():
    result = lib.sum_nt("tests/data/normalise-test.fasta", normalise=True)
    assert result == (
        ({"t1": "1676bc5970afaf54", "t2": "1676bc5970afaf54"}, "b29e3982cfea538e")
    )


def test_invalid_input_path():
    with pytest.raises(FileNotFoundError):
        lib.sum_nt(Path("tests/data/non-existent.fasta"))
