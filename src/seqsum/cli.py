import json as json_
from pathlib import Path

import defopt

from seqsum import lib


def sum(
    input: Path,
    *,
    alphabet: lib.Alphabet | None = None,
    bits: int = lib.default_bits,
    json: bool = False
):
    """
    Generate checksum(s) for sequences contained in fasta/fastq[.gz|.bz2] files or stdin

    :arg input: path to fasta/fastq file (or - for stdin)
    :arg alphabet: constrain input to a sequence alphabet
    :arg bits: displayed checksum length
    :arg json: output JSON
    """
    if str(input) == "-":
        checksums = lib.sum_stdin(alphabet=alphabet, bits=bits, stdout=not json)
    else:
        checksums = lib.sum_file(input, alphabet=alphabet, bits=bits, stdout=not json)
    if json:
        print(json_.dumps(checksums, indent=4))


def main():
    defopt.run(sum, no_negated_flags=True)
