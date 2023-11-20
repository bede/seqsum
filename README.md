[![Tests](https://github.com/bede/seqsum/actions/workflows/test.yml/badge.svg)](https://github.com/bede/seqsum/actions/workflows/test.yml) [![PyPI version](https://img.shields.io/pypi/v/seqsum)](https://pypi.org/project/seqsum)

# Seqsum

Robust individual and aggregate checksums for nucleotide sequences. Accepts data from either standard input or `fast[a|q][.gz|.zst|.xz|.bz2]` files. Generates *individual* checksums for each sequence, and an *aggregate* checksum-of-checksums for a collection of sequences. Warnings are shown for duplicate sequences and within-collection checksum collisions at the chosen bit depth. Sequences are uppercased prior to hashing with [xxHash](https://github.com/ifduyue/python-xxhash) (`xxh3_128`) and may optionally be normalised to use only the characters `ACGTN-`. Read IDs and base quality scores do not inform the checksum. Outputs TSV or JSON to stdout.

A typical use case is for determining whether reordered, renamed or otherwise bit-inexact fasta/fastq files have equivalent sequence composition. Another use is generating the shortest possible collision-free identifiers for sequence collections.

## Install (Python 3.10+)

```bash
# Latest release
pip install seqsum

# Latest commit
git clone https://github.com/bede/seqsum
pip install ./seqsum

# Development
git clone https://github.com/bede/seqsum.git
cd seqsum
pip install --editable '.[dev]'
pytest
```



## CLI usage

```bash
# Fasta with one record
$ seqsum nt MN908947.fasta
Processed 1 record(s) (1.20kit/s)
MN908947.3	ca5e95436b957f93

# Fasta with two records
$ seqsum nt MN908947-BA_2_86_1.fasta
Processed 2 record(s) (1.46kit/s)
MN908947.3	ca5e95436b957f93
BA.2.86.1		d5f014ee6745cb77
aggregate	837cfd6836b9a406

# Fastq (gzipped) with 1m records, including identical sequences, redirected to file
$ seqsum nt illumina.r12.fastq.gz > checksums.tsv
Processed 1000000 records (317kit/s)
INFO: Found duplicate sequences

# Fasta via stdin, progress hidden
% cat MN908947.fasta | seqsum nt --no-progress -
MN908947.3	ca5e95436b957f93
```

```bash
$ seqsum nt -h
usage: seqsum nt [-h] [--normalise] [--strict] [--bits BITS] [--output {individual,aggregate,both}] [--json]
                 [--progress | --no-progress]
                 input

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
  --normalise           replace U with T and characters other than ACGT- with N
                        (default: False)
  --strict              raise error for characters other than ABCDGHKMNRSTVWY-
                        (default: False)
  --bits BITS           displayed checksum length
                        (default: 64)
  --output {individual,aggregate,both}
                        output individual checksums, the aggregate checksum, or both
                        (default: both)
  --json                output JSON
                        (default: False)
  --progress, --no-progress
                        show progress and speed
                        (default: True)
```



## Python usage

```python
from seqsum import lib

fasta_contents = ">read1\nACGT"
checksums, aggregate_checksum = lib.sum_nt(fasta_contents)
print(checksums)
```

