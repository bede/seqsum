import hashlib
from pathlib import Path

import pyfastx
import xxhash


def sum_bytes_or_file(input_: str | Path, function: str) -> str:
    if Path(input_).exists():
        hex_digest = sum_file(input_, function=function)
    else:
        hex_digest = sum_bytes(input_, function=function)
    return hex_digest


def sum_bytes(input_: bytes, function: str) -> str:
    return generate_hash(input_.encode(), function=function)


def sum_file(input_: Path, function: str):
    for name, seq in pyfastx.Fasta(str(input_), build_index=False):
        break
    return generate_hash(seq.encode(), function=function)


def generate_hash(input_bytes, function: str) -> str:
    names_hash_funcs = dict(xxh128=xxhash.xxh128, sha256=hashlib.sha256)
    hash_func = names_hash_funcs[function]
    hex_digest = hash_func(input_bytes).hexdigest()
    return hex_digest
