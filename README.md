[![Tests](https://github.com/bede/seqsum/actions/workflows/test.yml/badge.svg)](https://github.com/bede/seqsum/actions/workflows/test.yml)

# Seqsum

Generates record-level checksums for biological sequences, ignoring record IDs. Checksums are generated for each record and  Also generates checksums for sets of records  Performs no normalisation or validation by default, but may be constrained to nucleotide or amino acid alphabets. Generates checksums for each record in a FASTA/FASTQ file and finally a checksum of checksum . Warns about duplicates and hash collisions by default.



## Install (Python 3.10+)

```
# Latest release
pip install seqsum

# From main branch
git clone https://github.com/bede/seqsum
pip install ./seqsum

# Development
git clone https://github.com/bede/seqsum.git
cd seqsum
pip install --editable ./
pytest
```



## Usage

```
% seqsum --help
usage: seqsum [-h] [-a {bytes,nt,aa}] [-b BITS] [-j] [--version] input

Generate checksum(s) for sequences contained in fasta/fastq[.gz|.zst|.xz|.bz2] files or stdin

positional arguments:
  input                 path to fasta/q file (or - for stdin)

options:
  -h, --help            show this help message and exit
  -a {bytes,nt,aa}, --alphabet {bytes,nt,aa}
                        constraint for sequence alphabet
                        (default: bytes)
  -b BITS, --bits BITS  displayed checksum length
                        (default: 64)
  -j, --json            output JSON
                        (default: False)
  --version             show program's version number and exit
```
