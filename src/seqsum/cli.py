import json as json_
from pathlib import Path

import defopt

from seqsum import lib


def nt(
    input: Path,
    *,
    normalise: bool = False,
    strict: bool = False,
    bits: int = lib.default_bits,
    json: bool = False,
    progress: bool = True,
):
    """
    Robust individual and collective checksums for nucleotide sequences. Accepts input
    from stdin or fast[a|q][.gz|.zst|.xz|.bz2] files. Generates checksums for each
    sequence, and a checksum of checksums given multiple records. Warnings are shown
    for duplicate sequences and within-collection checksum collisions at the chosen
    bit depth. Sequences are uppercased before hashing with xxh3_128 and may
    optionally be normalised to contain only the characters ACGTN-

    :arg input: path to fasta/q file (or - for stdin)
    :arg normalise: replace U with T and characters other than ACGT- with N
    :arg strict: raise error for characters other than ABCDGHKMNRSTVWY-
    :arg alphabet: constraint for sequence alphabet
    :arg bits: displayed checksum length
    :arg json: output JSON
    :arg progress: show progress and speed
    """
    checksums, checksum_of_checksums = lib.sum_nt(
        input, normalise=normalise, strict=strict, bits=bits, progress=progress
    )
    if checksum_of_checksums:
        checksums["sum-of-sums"] = checksum_of_checksums  # Combine for printing
    if json:
        print(json_.dumps(checksums, indent=4))
    else:
        for k, v in checksums.items():
            print(f"{k}\t{v}")


def main():
    defopt.run({"nt": nt}, no_negated_flags=True)
