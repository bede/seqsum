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
    # output: Literal["individual", "aggregate", "both"] = "both",
    individual: bool = False,
    aggregate: bool = False,
    json: bool = False,
    progress: bool = False,
):
    """
    Robust individual and aggregate checksums for nucleotide sequences. Accepts input
    from either stdin or fast[a|q][.gz|.zst|.xz|.bz2] files. Generates individual
    checksums for each sequence, and an aggregate checksum-of-checksums for a
    collection of sequences. Warnings are shown for duplicate sequences and
    within-collection checksum collisions at the chosen bit depth. Sequences are
    uppercased prior to hashing with xxHash and may optionally be normalised to use only
    the characters ACGTN-. Read IDs and base quality scores do not inform the checksum

    :arg input: path to fasta/q file (or - for stdin)
    :arg normalise: replace U with T and characters other than ACGT- with N
    :arg strict: raise error for characters other than ABCDGHKMNRSTVWY-
    :arg alphabet: constraint for sequence alphabet
    :arg bits: displayed checksum length
    :arg individual: output only individual checksums
    :arg aggregate: output only aggregate checksum
    :arg json: output JSON
    :arg progress: show progress and speed
    """
    checksums, aggregate_checksum = lib.sum_nt(
        input, normalise=normalise, strict=strict, bits=bits, progress=progress
    )
    if individual and not aggregate:
        pass
    elif aggregate and not individual:
        if aggregate_checksum:
            checksums = {"aggregate": aggregate_checksum}
        else:
            raise ValueError("Aggregate checksum unavailable")
    else:
        if aggregate_checksum:
            if "aggregate" not in checksums:
                checksums["aggregate"] = aggregate_checksum
            else:
                raise ValueError("A record named aggregate already exists")
    if json:
        print(json_.dumps(checksums, indent=4))
    else:
        for k, v in checksums.items():
            print(f"{k}\t{v}")


def main():
    defopt.run({"nt": nt}, no_negated_flags=True)
