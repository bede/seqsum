import enum
import logging
import sys
from pathlib import Path

import dnaio
import pyfastx
import xxhash


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


alphabets = {
    # Includes "-" as optimisation; these are stripped prior to hashing
    "nt": set("ABCDGHKMNRSTVWY") | set("-"),  # Bio.Alphabet.IUPAC.IUPACAmbiguousDNA
    "aa": set("*ACDEFGHIKLMNPQRSTVWY")
    | set("-"),  # Bio.Alphabet.IUPAC.ExtendedIUPACProtein
}
Alphabet = enum.Enum("Alphabet", list(alphabets.keys()))

default_bits = 64


class AlphabetError(Exception):
    def __init__(self, message="Record(s) contain characters not in alphabet"):
        super().__init__(message)


class BitLengthError(Exception):
    def __init__(self, message="Bit depth must be a multiple of 4 between 4 and 128"):
        super().__init__(message)


def validate_bits(bits: int) -> None:
    if not 4 < bits < 128 or bits % 4 != 0:
        raise BitLengthError


def truncate(checksums: dict[str, str], bits: int = default_bits) -> dict[str, str]:
    chars_to_keep = int(bits / 4)
    return {k: v[:chars_to_keep] for k, v in checksums.items()}


def normalise(input: str) -> str:
    return input.upper().replace("-", "")


def sum_bytes(
    input: bytes, alphabet: Alphabet | None = None, bits: int = default_bits
) -> str:
    if not set(input) <= alphabets[alphabet.name]:
        raise AlphabetError
    return truncate(generate_checksum(input.encode()), bits=bits)


def sum_file(
    input: Path,
    alphabet: Alphabet | None = None,
    bits: int = default_bits,
    stdout: bool = False,
) -> dict[str, str]:
    logging.info(f"Using file {input}")
    validate_bits(bits)
    chars_to_keep = int(bits / 4)
    checksums = {}
    # fa = pyfastx.Fasta(str(input), uppercase=True)
    # print(fa.composition)
    # print(dir(fa))
    # for name, seq in fa:
    for name, seq in pyfastx.Fasta(str(input), build_index=False, uppercase=True):
        # for record in dnaio.open(str(input)):
        #     name, seq = record.name, record.sequence

        if alphabet and not set(seq) <= alphabets[alphabet.name]:
            raise AlphabetError()
        checksum = generate_checksum(seq.encode())
        checksums[name] = checksum
        if stdout:
            print(f"{name}\t{checksum[:chars_to_keep]}")
    if len(checksums) > 1:
        checksums["ALL"] = generate_checksum_of_checksums(checksums)
        if stdout:
            print(f"ALL\t{checksums['ALL'][:chars_to_keep]}")
    return truncate(checksums, bits=bits)


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
    alphabet: Alphabet | None = None,
    bits: int = 64,
    stdout: bool = False,
) -> dict[str, str]:
    logging.info("Using stdin")
    validate_bits(bits)
    chars_to_keep = int(bits / 4)
    checksums = {}
    for name, seq in parse_fasta_from_stdin():
        if alphabet and not set(seq) <= alphabets[alphabet.name]:
            raise AlphabetError()
        checksum = generate_checksum(normalise(seq).encode())
        checksums[name] = checksum
        if stdout:
            print(f"{name}\t{checksum[:chars_to_keep]}")
    if len(checksums) > 1:
        checksums["ALL"] = generate_checksum_of_checksums(checksums)
        if stdout:
            print(f"ALL\t{checksums['ALL'][:chars_to_keep]}")
    return truncate(checksums, bits=bits)


def generate_checksum(input: bytes) -> str:
    hex_digest = xxhash.xxh3_128(input).hexdigest()
    return hex_digest


def generate_checksum_of_checksums(checksums: dict[str, str]) -> str:
    return generate_checksum("".join(sorted(checksums.values())))
