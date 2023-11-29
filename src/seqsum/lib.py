import io
import logging
import re

import dnaio
import xxhash

from pathlib import Path

from tqdm import tqdm


logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)


nt_alphabet = set("ABCDGHKMNRSTVWY-")  # IUPACAmbiguousDNA
aa_alphabet = set("*ACDEFGHIKLMNPQRSTVWY-")  # ExtendedIUPACProtein
default_bits = 64
normalise_to_t = str.maketrans("U", "T")
normalise_to_n = re.compile(r"[^BDHKMRSVWY]")


class DuplicateNameError(Exception):
    def __init__(self, names):
        self.names = names

    def __str__(self):
        return f"Sequence contains duplicated names: {', '.join(self.names)}"


class AlphabetError(Exception):
    def __init__(self, message="Sequence contains characters not in alphabet"):
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
        logging.warning("Found checksum collisions, consider increasing --bits")


def sum_nt(
    input: str,
    normalise: bool = False,
    strict: bool = False,
    bits: int = default_bits,
    progress: bool = False,
) -> tuple[dict[str, str], str | None]:
    validate_bits(bits)
    chars_to_keep = int(bits / 4)
    duplicate_names = set()
    checksums = {}
    aggregate_checksum = None
    # if type(input) == Path
    if not Path(input).is_file():
        if isinstance(input, Path):
            raise FileNotFoundError(f"Invalid input path: {input}")
        else:
            logging.info("Input is not a valid path, treating as string")
            input = io.BytesIO(input.encode())
    for record in tqdm(
        dnaio.open(input, open_threads=1),
        bar_format="Processed {n} record(s) ({rate_fmt})",
        disable=not progress,
        mininterval=0.25,
        unit_scale=True,
        leave=True,
    ):
        name, seq = record.name, record.sequence
        seq_chars = set(seq.upper())
        if strict and not seq_chars <= nt_alphabet:
            raise AlphabetError()
        if normalise:
            # logging.info(f"{seq=}")
            seq = normalise_nt(seq)
            # logging.info(f"normalised sequence {seq}")
        checksum = generate_checksum(seq)
        if name in checksums:
            duplicate_names.add(name)
        checksums[name] = checksum
    if len(checksums) > 1:
        aggregate_checksum = generate_aggregate_checksum(checksums)[:chars_to_keep]
    truncated_checksums = truncate(checksums, bits=bits)
    detect_duplicate_names(duplicate_names)
    detect_collisions(checksums, truncated_checksums)
    return truncated_checksums, aggregate_checksum


def normalise_nt(string: str) -> str:
    normalise_to_t = str.maketrans("U", "T")
    normalise_to_n = re.compile(r"[^ACGT-]")
    return normalise_to_n.sub("N", string.upper().translate(normalise_to_t))


def generate_checksum(string: str) -> str:
    # logging.info(f"{string=}")
    return xxhash.xxh3_128(string.upper().encode()).hexdigest()


def generate_aggregate_checksum(checksums: dict[str, str]) -> str:
    return generate_checksum("".join(sorted(checksums.values())))
