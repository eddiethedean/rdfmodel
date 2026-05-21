"""Canonicalize quads in memory via pyoxigraph.Dataset."""

from __future__ import annotations

from collections.abc import Iterable

from pyoxigraph import CanonicalizationAlgorithm, Dataset, Quad

_DEFAULT = CanonicalizationAlgorithm.UNSTABLE


def canonicalize_quads(
    quads: Iterable[Quad],
    *,
    algorithm: CanonicalizationAlgorithm = _DEFAULT,
) -> list[Quad]:
    """Return a canonical ordering of ``quads`` using :meth:`pyoxigraph.Dataset.canonicalize`.

    Use for diff snapshots of in-memory data. Blank-node labels from a persistent
    :class:`~pyoxigraph.Store` are not stable when graph shape changes.
    """
    dataset = Dataset()
    for quad in quads:
        dataset.add(quad)
    dataset.canonicalize(algorithm)
    return list(dataset)
