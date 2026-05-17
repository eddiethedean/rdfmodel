from examples.doc._models import Mailbox, Person

alice = Person(
    slug="alice",
    name="Alice",
    mbox=Mailbox(address="alice@example.org"),
)
graph = alice.to_graph()
restored = Person.from_graph(graph, alice.subject_uri())
print(restored.mbox.address if restored.mbox else None)
