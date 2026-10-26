"""Flat name of the first versions of `goldpan.operations`: the same code, kept for the existing notebooks.

See `goldpan.legacy`. New code imports `goldpan.operations`.
"""
from goldpan import legacy as _legacy
from goldpan import operations as _source

globals().update(_legacy.flat_namespace(_source, __name__))
