import enum
import logging
import sys
from pathlib import Path

import dnaio
import pyfastx
import xxhash


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


alphabets = {
    # Includes "-" as optimisation; stripped prior to hashing
    "bytes": set(),  # Avoids a type union, makes CLI help more intuitive
    "nt": set("ABCDGHKMNRSTVWY-"),  # Bio.Alphabet.IUPAC.IUPACAmbiguousDNA
    "aa": set("*ACDEFGHIKLMNPQRSTVWY-"),  # Bio.Alphabet.IUPAC.ExtendedIUPACProtein
}
Alphabet = enum.Enum("Alphabet", [k for k in alphabets.keys() if k != "bytes"])
Alphabet_cli = enum.Enum("Alphabet", list(alphabets.keys()))
default_bits = 64


class DuplicateNameError(Exception):
    def __init__(self, names):
        self.names = names

    def __str__(self):
        return f"Records contain duplicated names: {', '.join(self.names)}"


class AlphabetError(Exception):
    def __init__(self, message="Records contain characters not in alphabet"):
        super().__init__(message)


class BitLengthError(Exception):
    def __init__(self, message="Bit depth must be a multiple of 4 between 4 and 128"):
        super().__init__(message)


def validate_bits(bits: int) -> None:
    if not 4 <= bits <= 128 or bits % 4 != 0:
        raise BitLengthError


def truncate(checksums: dict[str, str], bits: int = default_bits) -> dict[str, str]:
    chars_to_keep = int(bits / 4)
    return {k: v[:chars_to_keep] for k, v in checksums.items()}


def normalise(input: str) -> str:
    return input.upper().replace("-", "")


def detect_duplicate_names(duplicate_names: list) -> None:
    if duplicate_names:
        raise DuplicateNameError(duplicate_names)


def detect_collisions(
    checksums: dict[str, str], truncated_checksums: dict[str, str]
) -> None:
    unique_checksums = len(set(checksums.values()))
    unique_truncated_checksums = len(set(truncated_checksums.values()))
    duplicate_sequences = unique_checksums < len(checksums)
    checksum_collisions = unique_truncated_checksums < unique_checksums
    if duplicate_sequences:
        logging.info("Found duplicate sequences")
    if checksum_collisions:
        logging.warning("Found checksum collisions. Consider increasing --bits")


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
    duplicate_names = set()
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
        if name in checksums:
            duplicate_names.add(name)
        checksums[name] = checksum
        if stdout:
            print(f"{name}\t{checksum[:chars_to_keep]}")
    if len(checksums) > 1:
        checksums["ALL"] = generate_checksum_of_checksums(checksums)
        if stdout:
            print(f"ALL\t{checksums['ALL'][:chars_to_keep]}")
    truncated_checksums = truncate(checksums, bits=bits)
    detect_duplicate_names(duplicate_names)
    detect_collisions(checksums, truncated_checksums)
    return truncated_checksums


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
    duplicate_names = set()
    checksums = {}
    for name, seq in parse_fasta_from_stdin():
        if alphabet and not set(seq) <= alphabets[alphabet.name]:
            raise AlphabetError()
        checksum = generate_checksum(normalise(seq).encode())
        if name in checksums:
            duplicate_names.add(name)
        checksums[name] = checksum
        if stdout:
            print(f"{name}\t{checksum[:chars_to_keep]}")
    if len(checksums) > 1:
        checksums["ALL"] = generate_checksum_of_checksums(checksums)
        if stdout:
            print(f"ALL\t{checksums['ALL'][:chars_to_keep]}")
    truncated_checksums = truncate(checksums, bits=bits)
    warn_duplicate_names(duplicate_names)
    warn_collisions(checksums, truncated_checksums)
    return truncated_checksums


def generate_checksum(input: bytes) -> str:
    hex_digest = xxhash.xxh3_128(input).hexdigest()
    return hex_digest


def generate_checksum_of_checksums(checksums: dict[str, str]) -> str:
    return generate_checksum("".join(sorted(checksums.values())))
