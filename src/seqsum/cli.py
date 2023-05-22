import json as json_
from pathlib import Path

import defopt

from seqsum import lib


def sum(
    input: str | Path,
    *,
    alphabet: lib.Alphabet = lib.default_alphabet,
    bits: int = lib.default_bits,
    json: bool = False
):
    """
    Generate checksum(s) for fasta/fastq sequences supplied as string, file, or stdin

    :arg input: string, fasta/fastq path, or stdin
    :arg alphabet: input sequence alphabet
    :arg bits: keep this many bits of the message digest
    :arg json: output json
    """
    checksums = lib.sum(input, alphabet=alphabet, bits=bits, stdout=not json)
    if json:
        print(json_.dumps(checksums, indent=4))


def main():
    defopt.run(sum, no_negated_flags=True)
