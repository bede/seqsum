import enum
import logging
import re
import sys

import dnaio
import xxhash

from pathlib import Path
from typing import Literal

from tqdm import tqdm

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


alphabets = {
    # Includes "-" as optimisation; stripped prior to hashing
    "none": None,  # Avoids a type union, makes CLI help more intuitive
    "nt": set("ABCDGHKMNRSTVWY-"),  # Bio.Alphabet.IUPAC.IUPACAmbiguousDNA
    "aa": set("*ACDEFGHIKLMNPQRSTVWY-"),  # Bio.Alphabet.IUPAC.ExtendedIUPACProtein
}
Alphabet = enum.Enum("Alphabet", [k for k in alphabets.keys() if k != "none"])
Alphabet_cli = enum.Enum("Alphabet", list(alphabets.keys()))
default_bits = 64

normalise_to_t = str.maketrans("U", "T")
normalise_to_n = re.compile(r"[^BDHKMRSVWY]")


class DuplicateNameError(Exception):
    def __init__(self, names):
        self.names = names

    def __str__(self):
        return f"Record contains duplicated names: {', '.join(self.names)}"


class AlphabetError(Exception):
    def __init__(self, message="Record contains characters not in alphabet"):
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


def sum_file(
    input: Path,
    normalise: bool = False,
    alphabet: Alphabet | None = None,
    bits: int = default_bits,
    stdout: bool = False,
) -> dict[str, str]:
    validate_bits(bits)
    chars_to_keep = int(bits / 4)
    duplicate_names = set()
    checksums = {}

    # fa = pyfastx.Fasta(str(input), uppercase=True)
    # for name, seq in fa:
    # for name, seq in pyfastx.Fasta(str(input), build_index=False, uppercase=True):
    # for record in parse_fastx_file(str(input)):
    #     name, seq = record.id, record.seq

    alphabet_chars = alphabets[alphabet.name] if alphabet else None
    for record in dnaio.open(input, open_threads=1):
        name, seq = record.name, record.sequence
        seq_chars = set(seq.upper())
        if alphabet and not seq_chars <= alphabet_chars:
            raise AlphabetError()
        checksum = generate_checksum(seq, normalise=normalise)
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
    alphabet_chars = alphabets.get(alphabet.name)
    for name, seq in parse_fasta_from_stdin():
        seq_chars = set(seq)
        if alphabet and not seq_chars <= alphabet_chars:
            raise AlphabetError()
        checksum = generate_checksum(seq)
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


def normalise(string: str, alphabet: Literal["nt", "aa"]) -> str:
    if alphabet == "nt":
        return normalise_to_n.sub("N", string.upper().translate(normalise_to_t))
    elif alphabet == "aa":
        return normalise_to_n.sub("N", string.upper())
    else:
        raise ValueError(f"Unknown alphabet: {alphabet}")


def generate_checksum(string: str, normalise: bool = False) -> str:
    # if normalise:
    return xxhash.xxh3_128(string.upper().encode()).hexdigest()


def generate_checksum_of_checksums(checksums: dict[str, str]) -> str:
    return generate_checksum("".join(sorted(checksums.values())))
