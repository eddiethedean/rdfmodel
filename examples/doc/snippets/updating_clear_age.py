from rdflib import URIRef

from examples.doc._models import FOAF_NS, Person
from triplemodel import sync_to_graph

alice = Person(slug="alice", name="Alice", age=30)
graph = alice.to_graph()
subj = URIRef(alice.subject_uri())
before = len(list(graph.objects(subj, URIRef(f"{FOAF_NS}age"))))
alice.age = None
sync_to_graph(alice, graph, mode="replace")
after = len(list(graph.objects(subj, URIRef(f"{FOAF_NS}age"))))
print(f"age triples before: {before}")
print(f"age triples after: {after}")
