Codegen (experimental)
======================

``triplemodel-codegen`` generates stub :class:`~triplemodel.TripleModel` classes from OWL/RDFS ontologies.

Limitations
-----------

- Only ``owl:DatatypeProperty`` and ``owl:ObjectProperty`` are emitted (plain ``rdf:Property`` is ignored).
- All properties are typed as ``str``; ``rdfs:range`` is not read.
- Every class gets ``id_field = "slug"`` and a ``slug: str`` field.
- Duplicate local field names (different predicate IRIs) keep the first property only (a ``UserWarning`` is emitted).
- Multiple ``rdfs:subClassOf`` parents: last parent wins in the emitted hierarchy.

Missing ontology files raise :exc:`FileNotFoundError` when the path has a known suffix (``.ttl``, ``.owl``, etc.).

.. automodule:: triplemodel.codegen
   :members:
   :undoc-members:

.. automodule:: triplemodel.codegen.cli
   :members:
