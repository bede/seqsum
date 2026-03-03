[![Tests](https://github.com/bede/seqsum/actions/workflows/test.yml/badge.svg)](https://github.com/bede/seqsum/actions/workflows/test.yml)

# Seqsum

> [!WARNING]  
> Seqsum was rewritten in Rust in 0.3.0. The original Python version of seqsum and how to use is archived in the [`python`](https://github.com/bede/seqsum/tree/python) branch. It remains available on PyPI.

Robust checksums for nucleotide sequences. Accepts one or more `fast[a|q][.gz|.zst]` files or standard input. Generates an *aggregate* checksum for each input file by default, similar to `md5sum`/`sha256sum`. Warnings are shown for duplicate sequences and within-collection checksum collisions at the selected bit depth. Sequences are uppercased before hashing with [RapidHash](https://github.com/Nicoshev/rapidhash) (v3) and may be normalised (with `-n`) to use only `ACGTN-`. Read IDs and FASTQ base quality scores do not inform the checksum. Output is tab-delimited text to stdout.

By default, seqsum outputs one aggregate checksum per file. Use `--individual` (`-i`) for per-record checksums, or `--all` (`-a`) for both individual and aggregate checksums. These flags are mutually exclusive.

## Install

```bash
cargo install seqsum
```

## Development

```bash
git clone https://github.com/bede/seqsum.git
cd seqsum
cargo test
```

## Command line usage

```bash
# Default: aggregate checksum per file
$ seqsum tests/data/MN908947.fasta
33ba13564e0a63e3	tests/data/MN908947.fasta

# Multiple files
$ seqsum tests/data/MN908947.fasta tests/data/MN908947-BA_2_86_1.fasta
33ba13564e0a63e3	tests/data/MN908947.fasta
d3a94eb82357ece5	tests/data/MN908947-BA_2_86_1.fasta

# Stdin
$ cat tests/data/MN908947.fasta | seqsum
33ba13564e0a63e3	-

# Individual per-record checksums
$ seqsum -i tests/data/MN908947-BA_2_86_1.fasta
33ba13564e0a63e3	MN908947.3
9fef3b61d54d8902	BA.2.86.1

# All: individual checksums + aggregate
$ seqsum -a tests/data/MN908947-BA_2_86_1.fasta
33ba13564e0a63e3	MN908947.3	tests/data/MN908947-BA_2_86_1.fasta
9fef3b61d54d8902	BA.2.86.1	tests/data/MN908947-BA_2_86_1.fasta
d3a94eb82357ece5	sum	tests/data/MN908947-BA_2_86_1.fasta

```

**Built-in help**

```bash
$ seqsum -h
```

