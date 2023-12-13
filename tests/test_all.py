import logging
import subprocess

from pathlib import Path

import pytest

import dnaio

from seqsum import lib

data_dir = Path("tests/data")


def run(cmd, cwd=data_dir):  # Helper for CLI testing
    return subprocess.run(
        cmd, cwd=cwd, shell=True, check=True, text=True, capture_output=True
    )


def test_version_cli():
    run("seqsum --version")


def test_single_record():
    assert lib.sum_nt("tests/data/MN908947.fasta") == (
        {"MN908947.3": "ca5e95436b957f93"},
        None,
    )


def test_single_record_cli():
    assert run("seqsum nt MN908947.fasta").stdout == "MN908947.3\tca5e95436b957f93\n"


def test_multiple_records():
    assert lib.sum_nt("tests/data/MN908947-BA_2_86_1.fasta") == (
        {"MN908947.3": "ca5e95436b957f93", "BA.2.86.1": "d5f014ee6745cb77"},
        "837cfd6836b9a406",
    )


def test_multiple_records_cli():
    assert run("seqsum nt MN908947-BA_2_86_1.fasta").stdout == (
        "MN908947.3\tca5e95436b957f93\n"
        "BA.2.86.1\td5f014ee6745cb77\n"
        "aggregate\t837cfd6836b9a406\n"
    )


def test_normalise():
    result = lib.sum_nt(Path("tests/data/normalise.fasta"), normalise=True)
    assert result == (
        ({"t1": "1676bc5970afaf54", "t2": "1676bc5970afaf54"}, "b29e3982cfea538e")
    )


def test_strict_pass():
    result = lib.sum_nt(Path("tests/data/strict-pass.fasta"), strict=True)
    assert result == (({"pass": "a727e12ce46c16e3"}, None))


def test_exc_strict_fail():
    with pytest.raises(lib.AlphabetError):
        lib.sum_nt(Path("tests/data/strict-fail.fasta"), strict=True)


def test_exc_invalid_path():
    with pytest.raises(FileNotFoundError):
        lib.sum_nt(Path("tests/data/non-existent.fasta"))


def test_exc_invalid_string_input():
    with pytest.raises(dnaio.exceptions.UnknownFileFormat):
        lib.sum_nt("<invalid fasta\nACGT")


def test_exc_duplicate_names():
    with pytest.raises(lib.DuplicateNameError):
        lib.sum_nt(Path("tests/data/duplicate-names.fasta"), strict=True)


def test_exc_invalid_bit_depth():
    with pytest.raises(lib.BitDepthError):
        lib.sum_nt(Path("tests/data/MN908947.fasta"), bits=9)


def test_logging_duplicate_sequences(caplog):
    with caplog.at_level(logging.INFO):
        lib.sum_nt(Path("tests/data/duplicate-sequences.fasta"))
        found = False
        for record in caplog.records:
            print(record)
            if "Found duplicate sequences" in record.msg:
                found = True
        assert found


def test_logging_collisions(caplog):
    with caplog.at_level(logging.WARNING):
        lib.sum_nt(Path("tests/data/collision.fasta"), bits=4)
        found = False
        for record in caplog.records:
            print(record)
            if "Found checksum collisions" in record.msg:
                found = True
        assert found
