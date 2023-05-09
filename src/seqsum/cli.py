from pathlib import Path

import defopt

from seqsum import lib


def sum(input: str | Path, *, function: str = "xxh128"):
    """
    Generate a checksum from the supplied string or path

    :arg input: string or path of input
    :arg function: hash
    """
    hex_digest = lib.sum_bytes_or_file(input, function=function)
    print(hex_digest)


def main():
    defopt.run(
        sum,
    )
