import enum
import logging
from pathlib import Path

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
    pass


def normalise(
    input: bytes,
) -> bytes:
    return input.strip().upper().encode()


def sum(
    input: bytes | Path,
    alphabet: Alphabet = Alphabet.bio,
    bits: int = 64,
    stdout: bool = False,
) -> dict[str, str]:
    checksum_of_checksums = {}
    if 4 < bits > 128 or bits % 4 != 0:
        raise BitDepthError(
            "Specified bits must be integer multiple of 4 between 4 and 128"
        )
    if Path(input).exists():
        logging.info(f"Mode: file, alphabet: {alphabet.name}")
        checksums = sum_file(input, alphabet=alphabet, bits=bits, stdout=stdout)
        checksum_of_checksums = {
            "ALL": generate_checksum_of_checksums(checksums, bits=bits)
        }
        if len(checksums) > 1 and stdout:
            print(f"ALL\t{checksum_of_checksums['ALL']}")
    else:
        logging.info(f"Mode: string, alphabet: {alphabet.name}")
        checksums = {"": sum_bytes(input, alphabet=alphabet, bits=bits)}
    return {**checksums, **checksum_of_checksums}


def sum_bytes(
    input: bytes, alphabet: Alphabet = default_alphabet, bits: int = default_bits
) -> str:
    if not set(input) <= alphabets[alphabet.name]:
        raise AlphabetError("Error")
    return generate_checksum(input.encode(), bits=bits)


def sum_file(
    input: Path,
    alphabet: Alphabet = default_alphabet,
    bits: int = default_bits,
    stdout: bool = False,
) -> dict[str, str]:
    checksums = {}
    # fa = pyfastx.Fasta(str(input))
    # print(fa.composition)
    import dnaio

    for record in dnaio.open(str(input)):
        checksums[record.name] = generate_checksum(record.sequence.encode(), bits=bits)
        if stdout:
            print(f"{record.name}\t{checksums[record.name]}")
    return checksums

    # for name, seq in pyfastx.Fasta(str(input), build_index=False):
    #     checksums[name] = generate_checksum(seq.encode(), bits=bits)
    #     if stdout:
    #         print(f"{name}\t{checksums[name]}")
    # return checksums


def generate_checksum(inputbytes, bits: int = default_bits) -> str:
    hash_func = xxhash.xxh3_128
    chars_to_keep = int(bits / 4)
    hex_digest = hash_func(inputbytes).hexdigest()[:chars_to_keep]
    # hex_digest = hash_func(inputbytes).digest()
    return hex_digest


def generate_checksum_of_checksums(checksums: dict[str, str], bits: int) -> str:
    return generate_checksum("".join(sorted(checksums.values())), bits=bits)
