[![Tests](https://github.com/bede/seqsum/actions/workflows/test.yml/badge.svg)](https://github.com/bede/seqsum/actions/workflows/test.yml)

# Seqsum

Robust individual and collective checksums for nucleotide sequences. Accepts input from stdin or `fast[a|q][.gz|.zst|.xz|.bz2]` files. Generates checksums for each sequence, and a checksum of checksums given multiple records. Warnings are shown for duplicate sequences and within-collection checksum collisions at the chosen bit depth. Sequences are uppercased before hashing with `xxh3_128` and may optionally be normalised to contain only the characters `ACGTN-`.



## Install (Python 3.10+)

```bash
# Latest release
pip install seqsum

# From main branch
git clone https://github.com/bede/seqsum
pip install ./seqsum

# Development
git clone https://github.com/bede/seqsum.git
cd seqsum
pip install --editable '.[dev]'
pytest
```



## Usage

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
sum-of-sums	837cfd6836b9a406

# Fastq (gzipped) with 1m records, including identical sequences, redirected to file
$ seqsum nt illumina.r12.fastq.gz > checksums.tsv
Processed 1000000 records (317kit/s)
INFO: Found duplicate sequences

# Fasta via stdin
% cat MN908947.fasta | seqsum nt --no-progress -
MN908947.3	ca5e95436b957f93
```



```bash
$ seqsum nt -h
usage: seqsum nt [-h] [-n] [-s] [-b BITS] [-j] [-p | --progress | --no-progress] input

Robust individual and collective checksums for nucleotide sequences. Accepts input
from stdin or fast[a|q][.gz|.zst|.xz|.bz2] files. Generates checksums for each
sequence, and a checksum of checksums given multiple records. Warnings are shown
for duplicate sequences and within-collection checksum collisions at the chosen
bit depth. Sequences are uppercased before hashing with xxh3_128 and may
optionally be normalised to contain only the characters ACGTN-

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
  -j, --json            output JSON
                        (default: False)
  -p, --progress, --no-progress
                        show progress and speed
                        (default: True)
```
