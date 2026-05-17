from examples.doc._models import Person

alice = Person(slug="alice", name="Alice", age=30)
graph = alice.to_graph()
print(alice.subject_uri())
