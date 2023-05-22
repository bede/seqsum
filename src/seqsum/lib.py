import enum
import logging
import sys
from pathlib import Path

import dnaio
import pyfastx
import xxhash


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


alphabets = {
    "bio": "*ABCDEFGHIKLMNPQRSTVWY-",  # union(nt, aa)
    "nt": "ABCDGHKMNRSTVWY",  # Bio.Alphabet.IUPAC.IUPACAmbiguousDNA
    "aa": "*ACDEFGHIKLMNPQRSTVWY",  # Bio.Alphabet.IUPAC.ExtendedIUPACProtein
}
Alphabet = enum.Enum("Alphabet", list(alphabets.keys()))
default_alphabet = Alphabet.bio

default_bits = 64


class AlphabetError(Exception):
    pass


class BitDepthError(Exception):
    def __init__(self, message="Bit depth must be a multiple of 4 between 4 and 128"):
        super().__init__(message)


def validate_bits(bits: int) -> None:
    if not 4 < bits < 128 or bits % 4 != 0:
        raise BitDepthError


def normalise(
    input: bytes,
) -> bytes:
    return input.strip().upper().encode()


def truncate_bits(
    checksums: dict[str, str], bits: int = default_bits
) -> dict[str, str]:
    chars_to_keep = int(bits / 4)
    return {k: v[:chars_to_keep] for k, v in checksums.items()}


def sum_bytes(
    input: bytes, alphabet: Alphabet = default_alphabet, bits: int = default_bits
) -> str:
    if not set(input) <= alphabets[alphabet.name]:
        raise AlphabetError("Error")
    return truncate_bits(generate_checksum(input.encode()), bits=bits)


def sum_file(
    input: Path,
    alphabet: Alphabet = default_alphabet,
    bits: int = default_bits,
    stdout: bool = False,
) -> dict[str, str]:
    logging.info(f"Using file {input}")
    validate_bits(bits)
    chars_to_keep = int(bits / 4)
    checksums = {}
    for record in dnaio.open(str(input)):
        checksums[record.name] = generate_checksum(record.sequence.encode())
        if stdout:
            print(f"{record.name}\t{checksums[record.name][:chars_to_keep]}")
    if len(checksums) > 1:
        checksums["ALL"] = generate_checksum_of_checksums(checksums)
        if stdout:
            print(f"ALL\t{checksums['ALL'][:chars_to_keep]}")
    return truncate_bits(checksums, bits=bits)

    # for name, seq in pyfastx.Fasta(str(input), build_index=False):
    #     checksums[name] = generate_checksum(seq.encode(), bits=bits)
    #     if stdout:
    #         print(f"{name}\t{checksums[name]}")
    # return checksums


def parse_fasta_from_stdin():
    name, sequence = None, []
    for line in sys.stdin:
        line = line.rstrip()
        if line.startswith(">"):
            if name:
                yield (name, "".join(sequence))
            name, sequence = line[1:], []
        else:
            sequence.append(line)
    if name:
        yield (name, "".join(sequence))


def sum_stdin(
    alphabet: Alphabet = Alphabet.bio,
    bits: int = 64,
    stdout: bool = False,
) -> dict[str, str]:
    logging.info("Using stdin")
    validate_bits(bits)
    chars_to_keep = int(bits / 4)
    checksums = {}
    for name, seq in parse_fasta_from_stdin():
        checksums[name] = generate_checksum(seq.encode())
        if stdout:
            print(f"{name}\t{checksums[name][:chars_to_keep]}")
    if len(checksums) > 1:
        checksums["ALL"] = generate_checksum_of_checksums(checksums)
        if stdout:
            print(f"ALL\t{checksums['ALL'][:chars_to_keep]}")
    return truncate_bits(checksums, bits=bits)


def generate_checksum(input: bytes) -> str:
    hex_digest = xxhash.xxh3_128(input).hexdigest()
    return hex_digest


def generate_checksum_of_checksums(checksums: dict[str, str]) -> str:
    return generate_checksum("".join(sorted(checksums.values())))
