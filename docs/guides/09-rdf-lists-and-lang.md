# RDF lists and language-tagged literals

TripleModel maps **`list[T]`** fields to ordered **`rdf:List`** structures and **`set[T]`** fields to multiple objects on one predicate.

## `list[T]` → `rdf:List`

Use a Python `list` when order matters and the graph should use an **`rdf:List`** head node (`rdf:first` / `rdf:rest`):

```python
nick: list[str] = rdf_field("foaf:nick", default_factory=list)
```

```{literalinclude} ../../examples/doc/snippets/rdf_list_nick.py
:language: python
```

Output:

```{literalinclude} ../../examples/doc/outputs/rdf_list_nick.txt
:language: text
```

Sync modes clear the entire list structure when the field is `None` or `[]`.

If the graph has **more than one `rdf:List` head** for the same predicate, import uses the **first** head only. Use `on_duplicate="error"` on import to surface ambiguous data; `"ignore"` suppresses the warning but does not merge lists.

## `set[T]` → multiple objects

Use a **`set`** when you want several objects on the same predicate without an RDF list (order not guaranteed):

```python
tag: set[str] = rdf_field("http://example.org/tag", default_factory=set)
```

See {doc}`03-multi-valued-fields` for sync and duplicate-object behaviour.

## Language tags

### `LangString`

```python
from triplemodel.terms.lang import LangString

title: LangString = rdf_field("http://purl.org/dc/terms/title")
doc = Document(slug="d1", title=LangString("Hello", "en"))
```

### `Annotated[str, Lang("en")]`

```python
from typing import Annotated
from triplemodel.terms.lang import Lang

title: Annotated[str, Lang("en")] = rdf_field("http://purl.org/dc/terms/title")
```

Export emits `Literal(..., lang=...)`; import restores the tag.

## Related

- {doc}`03-multi-valued-fields` — `set[T]` multi-object fields
- {doc}`../ROADMAP` — future literal and blank-node work
