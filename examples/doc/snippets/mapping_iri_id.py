from examples.doc._models import ExternalResource

resource = ExternalResource(
    uri="https://catalog.example.org/item/42",
    title="Widget",
)
print(resource.subject_uri())
