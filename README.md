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
usage: seqsum [-h] [-f FUNCTION] [--version] input

Generate a checksum from the supplied string or path

positional arguments:
  input                 string or path of input

options:
  -h, --help            show this help message and exit
  -f FUNCTION, --function FUNCTION
                        hash
                        (default: xxh128)
  --version             show program's version number and exit
```
