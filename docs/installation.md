# Installation

## Requirements

- Python **3.10** or newer
- [Pydantic](https://docs.pydantic.dev/) v2
- [rdflib](https://rdflib.readthedocs.io/) v7

## PyPI

```bash
pip install triplemodel
```

## From source

```bash
git clone https://github.com/eddiethedean/triplemodel.git
cd triplemodel
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Verify

```{literalinclude} ../examples/doc/snippets/installation_version.py
:language: python
```

Output:

```{literalinclude} ../examples/doc/outputs/installation_version.txt
:language: text
```

**Next:** {doc}`quickstart` or the full {doc}`guides/01-getting-started`.
