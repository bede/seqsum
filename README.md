[![Tests](https://github.com/bede/seqsum/actions/workflows/test.yml/badge.svg)](https://github.com/bede/seqsum/actions/workflows/test.yml)

# Seqsum

Robust checksums for nucleotide sequences. Accepts input from either standard input or `fast[a|q][.gz|.zst|.xz|.bz2]` files. Generates individual checksums for each sequence, plus an aggregate checksum for a collection. Warnings are shown for duplicate sequences and within-collection checksum collisions at the selected bit depth. Sequences are uppercased before hashing with [rapidhash](https://github.com/Nicoshev/rapidhash) (`v3`) and may be normalised (with `-n`) to use only `ACGTN-`. Read IDs and FASTQ base quality scores do not inform the checksum. Output is tab-delimited text to stdout.

By default, seqsum outputs individual checksums and, when there is more than one sequence, an aggregate checksum. This can be modified with `--individual` (`-i`) or `--aggregate` (`-a`).

Uses [`paraseq`](https://github.com/mbhall88/paraseq) for efficient FASTA/FASTQ parsing.

## Install

```bash
cargo install --path .
```

## Development

```bash
git clone https://github.com/bede/seqsum.git
cd seqsum
cargo test
cargo fmt --all --check
cargo clippy --all-targets -- -D warnings
```

## Command line usage

```bash
# Fasta with one record
$ seqsum tests/data/MN908947.fasta
33ba13564e0a63e3	MN908947.3

# Fasta with two records
$ seqsum tests/data/MN908947-BA_2_86_1.fasta
33ba13564e0a63e3	MN908947.3
9fef3b61d54d8902	BA.2.86.1
d3a94eb82357ece5	aggregate

# Fasta with two records, only show aggregate checksum
$ seqsum tests/data/MN908947-BA_2_86_1.fasta --aggregate
d3a94eb82357ece5	aggregate

# Fasta via stdin
$ cat tests/data/MN908947.fasta | seqsum -
33ba13564e0a63e3	MN908947.3

```

**Built-in help**

```bash
$ seqsum -h
```
