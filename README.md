# BW ILCD Network Interactive Client

[![PyPI](https://img.shields.io/pypi/v/bwilcd.svg)][pypi status]
[![Status](https://img.shields.io/pypi/status/bwilcd.svg)][pypi status]
[![Python Version](https://img.shields.io/pypi/pyversions/bwilcd)][pypi status]
[![License](https://img.shields.io/pypi/l/bwilcd)][license]

[![Read the documentation at https://bwilcd.readthedocs.io/](https://img.shields.io/readthedocs/bwilcd/latest.svg?label=Read%20the%20Docs)][read the docs]
[![Tests](https://github.com/haitham-ghaida/bwilcd/actions/workflows/python-test.yml/badge.svg)][tests]
[![Codecov](https://codecov.io/gh/haitham-ghaida/bwilcd/branch/main/graph/badge.svg)][codecov]

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)][pre-commit]
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)][black]

[pypi status]: https://pypi.org/project/bwilcd/
[read the docs]: https://bwilcd.readthedocs.io/
[tests]: https://github.com/haitham-ghaida/bwilcd/actions?workflow=Tests
[codecov]: https://app.codecov.io/gh/haitham-ghaida/bwilcd
[pre-commit]: https://github.com/pre-commit/pre-commit
[black]: https://github.com/psf/black

A command-line tool for interacting with ILCD Network nodes. This tool provides an interactive interface for browsing and downloading data stocks from ILCD Network nodes.

## Features

- Interactive command-line interface with colored output
- Connect to predefined or custom ILCD Network nodes
- Optional authentication support
- List and browse available data stocks
- Search and view datasets within stocks
- Download data stocks as ZIP files
- Progress bar for downloads
- Command shortcuts for common operations

## Installation

```bash
# Clone the repository
git clone https://github.com/bwi/bwilcd-cli.git
cd bwilcd-cli

# Install the package
pip install .
```

## Usage

Start the interactive client:

```bash
bwilcd
```

### Commands

When starting the client, you'll see a list of predefined nodes. You can:

- Connect to a node: `c <number>` or `connect <number>`
- Connect to a custom URL: `url <url>`
- Show help: `h` or `help`
- Quit: `q` or `quit`

After connecting to a node, you can:

- Select a stock: `sl <number>` or `select <number>`
- Download a stock: `d <number>` or `dd <number>`
- Go back: `b` or `back`
- Refresh stocks: `r` or `refresh`

When browsing a stock, you can:

- Search datasets: `s <query>` or `search <query>`
- List all datasets: `ll`
- Navigate pages: `n` or `next`, `p` or `prev`
- Download current stock: `d` or `dd`

## Examples

1. Connect to ProBas and list stocks:
```bash
bwilcd
> connect 1
```

2. Search for datasets in a stock:
```bash
bwilcd> select 1
bwilcd> search treatment
```

3. Download a stock:
```bash
bwilcd> dd 1
```


## Contributing

Contributions are very welcome.
To learn more, see the [Contributor Guide][Contributor Guide].

## License

Distributed under the terms of the [MIT license][License],
_bwilcd_ is free and open source software.

## Issues

If you encounter any problems,
please [file an issue][Issue Tracker] along with a detailed description.


<!-- github-only -->

[command-line reference]: https://bwilcd.readthedocs.io/en/latest/usage.html
[License]: https://github.com/haitham-ghaida/bwilcd/blob/main/LICENSE
[Contributor Guide]: https://github.com/haitham-ghaida/bwilcd/blob/main/CONTRIBUTING.md
[Issue Tracker]: https://github.com/haitham-ghaida/bwilcd/issues


## Building the Documentation

You can build the documentation locally by installing the documentation Conda environment:

```bash
conda env create -f docs/environment.yml
```

activating the environment

```bash
conda activate sphinx_bwilcd
```

and [running the build command](https://www.sphinx-doc.org/en/master/man/sphinx-build.html#sphinx-build):

```bash
sphinx-build docs _build/html --builder=html --jobs=auto --write-all; open _build/html/index.html
```