"""Flat name of the first versions of `goldpan.status`: the same code, kept for the existing notebooks.

See `goldpan.legacy`. New code imports `goldpan.status`.
"""
from goldpan import legacy as _legacy
from goldpan import status as _source

globals().update(_legacy.flat_namespace(_source, __name__))
