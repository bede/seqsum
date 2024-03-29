[![Tests](https://github.com/bede/seqsum/actions/workflows/test.yml/badge.svg)](https://github.com/bede/seqsum/actions/workflows/test.yml) [![PyPI version](https://img.shields.io/pypi/v/seqsum)](https://pypi.org/project/seqsum)

# Seqsum

Robust checksums for nucleotide sequences. Accepts data from either standard input or `fast[a|q][.gz|.zst|.xz|.bz2]` files. Generates *individual* checksums for each sequence, and an *aggregate* checksum-of-checksums for a collection of sequences. Warnings are shown for duplicate sequences and within-collection checksum collisions at the chosen bit depth. Sequences are uppercased prior to hashing with [xxHash](https://github.com/ifduyue/python-xxhash) (`xxh3_128`) and may be normalised (with `-n`) to use only the characters `ACGTN-`. Read IDs and FASTQ base quality scores do not inform the checksum. Outputs tab delimited text or JSON to stdout.

A typical use case is determining whether reordered, renamed or otherwise bit-inexact fasta/fastq files have equivalent sequence composition. Another use is generating the shortest possible collision-free identifiers for sequence collections.

By default, seqsum outputs both individual and aggregate checksums when supplied with more than one sequence. This can be modified with the flags `--individual` (`-i`) or `--aggregate` (`-a`).



## Install

Installation inside a clean Python 3.10+ virtualenv (or conda environment) is recommended. To open `.zst` archives, you will also need to `pip install zstandard`.

```bash
pip install seqsum
```



**Development install**

```# Development
git clone https://github.com/bede/seqsum.git
cd seqsum
pip install --editable '.[dev]'
pytest
```



## Command line usage

```bash
# Fasta with one record
$ seqsum nt MN908947.fasta
MN908947.3	ca5e95436b957f93

# Fasta with two records
$ seqsum nt MN908947-BA_2_86_1.fasta
MN908947.3	ca5e95436b957f93
BA.2.86.1		d5f014ee6745cb77
aggregate	837cfd6836b9a406

# Fasta with two records, only show the aggregate checksum
$ seqsum nt -a MN908947-BA_2_86_1.fasta
aggregate	837cfd6836b9a406

# Fasta via stdin
% cat MN908947.fasta | seqsum nt -
MN908947.3	ca5e95436b957f93

# Fastq (gzipped) with 1m records, redirected to file, with progress bar
$ seqsum nt illumina.r12.fastq.gz --progress > checksums.tsv
Processed 1000000 records (317kit/s)
INFO: Found duplicate sequences
```

**Built-in help**

```bash
$ seqsum nt -h                       
usage: seqsum nt [-h] [-n] [-s] [-b BITS] [-i] [-a] [-j] [-p] input

Robust individual and aggregate checksums for nucleotide sequences. Accepts input
from either stdin or fast[a|q][.gz|.zst|.xz|.bz2] files. Generates individual
checksums for each sequence, and an aggregate checksum-of-checksums for a
collection of sequences. Warnings are shown for duplicate sequences and
within-collection checksum collisions at the chosen bit depth. Sequences are
uppercased prior to hashing with xxHash and may optionally be normalised to use only
the characters ACGTN-. Read IDs and base quality scores do not inform the checksum

positional arguments:
  input                 path to fasta/q file (or - for stdin)

options:
  -h, --help            show this help message and exit
  -n, --normalise       replace U with T and characters other than ACGT- with N
                        (default: False)
  -s, --strict          raise error for characters other than ABCDGHKMNRSTVWY-
                        (default: False)
  -b BITS, --bits BITS  displayed checksum length
                        (default: 64)
  -i, --individual      output only individual checksums
                        (default: False)
  -a, --aggregate       output only aggregate checksum
                        (default: False)
  -j, --json            output JSON
                        (default: False)
  -p, --progress        show progress and speed
                        (default: False)
```



## Python usage

```python
from seqsum import lib

checksums, aggregate_checksum = lib.sum_nt(">read1\nACGT")
print(checksums)
# {'read1': '81db282b97e7dfd1'}
```

```python
from pathlib import Path
from seqsum import lib

fasta_path = Path("tests/data/MN908947-BA_2_86_1.fasta")
checksums, aggregate_checksum = lib.sum_nt(fasta_path)
print(checksums)
print(aggregate_checksum)
# {'MN908947.3': 'ca5e95436b957f93', 'BA.2.86.1': 'd5f014ee6745cb77'}
# 837cfd6836b9a406
```

