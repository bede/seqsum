[![Tests](https://github.com/bede/seqsum/actions/workflows/test.yml/badge.svg)](https://github.com/pha4ge/primaschema/actions/workflows/test.yml)

# Seqsum

Checksums for biological sequences. Under development.



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

Generate checksum(s) for sequences contained in fasta/fastq[.gz|.bz2] files or stdin

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
