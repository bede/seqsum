import subprocess
from pathlib import Path

from seqsum import lib

data_dir = Path("tests/data")


def run(cmd, cwd=data_dir):  # Helper for CLI testing
    return subprocess.run(
        cmd, cwd=cwd, shell=True, check=True, text=True, capture_output=True
    )


def test_cli_version():
    run("seqsum --version")


def test_cli_sars2_tsv():
    run("seqsum MN908947.fasta")
    run("seqsum MN908947.fasta --format json")


def test_sars2_xxh128():
    assert lib.sum_file("tests/data/MN908947.fasta", algorithm="xxh3_128") == {
        "MN908947.3": "ca5e95436b957f930fb185a5620e29c0"
    }


def test_sars2_sha256():
    assert lib.sum_file("tests/data/MN908947.fasta", algorithm="sha256") == {
        "MN908947.3": "7d5621cd3b3e498d0c27fcca9d3d3c5168c7f3d3f9776f3005c7011bd90068ca"
    }
