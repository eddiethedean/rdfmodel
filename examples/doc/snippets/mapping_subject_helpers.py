from triplemodel import id_from_subject_uri, subject_base

base = subject_base("http://example.org/people")
segment = id_from_subject_uri(
    "http://example.org/people",
    "http://example.org/people/alice",
)
print(base)
print(segment)
