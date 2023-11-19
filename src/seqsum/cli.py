import json as json_
from pathlib import Path

import defopt

from seqsum import lib


def sum(
    input: Path,
    *,
    normalise: bool = False,
    alphabet: lib.Alphabet_cli = lib.Alphabet_cli.none,
    bits: int = lib.default_bits,
    json: bool = False
):
    """
    Generate checksum(s) for sequences as fasta/fastq[.gz|.bz2] files or stdin.
    Automatically warns of duplicate sequences and checksum collisions.

    :arg input: path to fasta/q file (or - for stdin)
    :arg normalise: Replace non ACGT- characters with N
    :arg alphabet: constraint for sequence alphabet
    :arg bits: displayed checksum length
    :arg json: output JSON
    """
    alphabet = alphabet if alphabet != lib.Alphabet_cli.none else None
    if str(input) == "-":
        checksums = lib.sum_stdin(alphabet=alphabet, bits=bits, stdout=not json)
    else:
        checksums = lib.sum_file(
            input, normalise=normalise, alphabet=alphabet, bits=bits, stdout=not json
        )
    if json:
        print(json_.dumps(checksums, indent=4))


def main():
    defopt.run(sum, no_negated_flags=True)
