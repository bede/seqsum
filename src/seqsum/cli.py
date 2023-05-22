import json as json_
from pathlib import Path

import defopt

from seqsum import lib


def sum(
    input: Path,
    *,
    alphabet: lib.Alphabet = lib.default_alphabet,
    bits: int = lib.default_bits,
    json: bool = False
):
    """
    Generate checksum(s) for fasta/fastq sequences supplied as string, file, or stdin

    :arg input: path to fasta/fastq file (supports gzip, bzip2, xz or zst compression)
    :arg alphabet: input sequence alphabet
    :arg bits: keep this many bits of the message digest
    :arg json: output json rather
    """
    if str(input) == "-":
        checksums = lib.sum_stdin(alphabet=alphabet, bits=bits, stdout=not json)
    else:
        checksums = lib.sum_file(input, alphabet=alphabet, bits=bits, stdout=not json)
    if json:
        print(json_.dumps(checksums, indent=4))


def main():
    defopt.run(sum, no_negated_flags=True)
