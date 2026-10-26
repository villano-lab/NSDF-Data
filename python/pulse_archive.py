"""Flat name of the first versions of `goldpan.archive`: the same code, kept for the existing notebooks.

See `goldpan.legacy`. New code imports `goldpan.archive`.
"""
from goldpan import legacy as _legacy
from goldpan import archive as _source

globals().update(_legacy.flat_namespace(_source, __name__))
