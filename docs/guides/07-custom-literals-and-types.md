# Custom literals and types

TripleModel maps common scalars to XSD literals automatically. For `Decimal`, `UUID`, and `Enum`, built-in converters are registered. You can add your own types with the literal registry.

## Built-in support

| Python type | Notes |
|-------------|--------|
| `Decimal` | XSD decimal literal |
| `UUID` | Stored as string, parsed back to `UUID` |
| `Enum` | Uses `enum.value` as string |

```python
from decimal import Decimal
from enum import Enum
from triplemodel import TripleModel, rdf_field

class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Item(TripleModel):
    class Rdf:
        namespace = "http://example.org/items/"
        type_uri = "http://example.org/Item"
        id_field = "sku"

    sku: str
    price: Decimal = rdf_field("http://example.org/price")
    status: Status = rdf_field("http://example.org/status")

item = Item(sku="1", price=Decimal("9.99"), status=Status.ACTIVE)
restored = Item.from_graph(item.to_graph(), item.subject_uri())
```

## Register a custom type

```python
from rdflib import Literal, XSD
from triplemodel import register_literal_type

class Money:
    def __init__(self, amount: str):
        self.amount = amount

register_literal_type(
    Money,
    to_literal=lambda m: Literal(m.amount, datatype=XSD.decimal),
    from_literal=lambda lit: Money(str(lit)),
    datatype=str(XSD.decimal),
)
```

When `datatype` is provided, TripleModel also calls `rdflib.term.bind` so rdflib recognizes the Python type.

Registry lookup runs **before** generic XSD coercion in `python_to_term` / `term_to_python`.

## Enums

Subclass `enum.Enum` (or `StrEnum` on Python 3.11+). Import coerces the literal string to the enum member; export writes `member.value`.

**Next:** [Working with graphs →](08-working-with-graphs.md)
