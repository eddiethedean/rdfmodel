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

### `MultiLangString`

When one predicate carries **several** language-tagged literals (for example `rdfs:label@en` and `rdfs:label@fr`), use `MultiLangString` instead of `set[LangString]`:

```python
from triplemodel import MultiLangString, TripleModel, rdf_field
from triplemodel.vocab import RDFS

class Term(TripleModel):
    class Rdf:
        namespace = "http://example.org/terms/"
        id_field = "slug"

    slug: str
    label: MultiLangString = rdf_field(f"{RDFS}label")

term = Term(slug="t1", label=MultiLangString({"en": "Cat", "fr": "Chat"}))
```

Import collects every object on the predicate that has a `language` tag (untagged literals are skipped). Language tags are normalized to lowercase on import (for example `EN` and `en` map to the same key). Export writes one triple per map entry. Conflicting values for the **same** language respect `on_duplicate` on `from_graph` (`"error"`, `"warn"`, or keep the first).

Pydantic accepts a plain `dict[str, str]` for the field value. Prefer **`MultiLangString`** when you want one field for a language map; use **`set[LangString]`** only if you need an unordered bag of tags without a single keyed map API.

### Helpers and `MultiLangString`

- **`graph_value(graph, subject, field)`** on a `MultiLangString` field returns a **`MultiLangString`** instance.
- **`objects_for_field`** returns a **`list[LangString]`** (one per language), not a `MultiLangString`.
- **`graph_set`** does not accept a `MultiLangString` value; update the model field and use **`sync_to_graph`** or assign on the instance before export.

## Related

- {doc}`03-multi-valued-fields` — `set[T]` multi-object fields
- {doc}`../ROADMAP` — future literal and blank-node work
