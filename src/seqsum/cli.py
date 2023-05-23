import json as json_
from pathlib import Path

import defopt

from seqsum import lib


def sum(
    input: Path,
    *,
    alphabet: lib.Alphabet_cli = lib.Alphabet_cli.bytes,
    bits: int = lib.default_bits,
    json: bool = False
):
    """
    Generate checksum(s) for sequences as fasta/fastq[.gz|.bz2] files or stdin

    :arg input: path to fasta/q file (or - for stdin)
    :arg alphabet: constraint for sequence alphabet
    :arg bits: displayed checksum length
    :arg json: output JSON
    """
    alphabet = alphabet if alphabet != lib.Alphabet_cli.bytes else None
    if str(input) == "-":
        checksums = lib.sum_stdin(alphabet=alphabet, bits=bits, stdout=not json)
    else:
        checksums = lib.sum_file(input, alphabet=alphabet, bits=bits, stdout=not json)
    if json:
        print(json_.dumps(checksums, indent=4))


def main():
    defopt.run(sum, no_negated_flags=True)
