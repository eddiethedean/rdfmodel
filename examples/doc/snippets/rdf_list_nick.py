from examples.doc._models import Person

person = Person(slug="alice", name="Alice", nick=["Al", "Alice"])
restored = Person.from_graph(person.to_graph(), person.subject_uri())
print(restored.nick)
