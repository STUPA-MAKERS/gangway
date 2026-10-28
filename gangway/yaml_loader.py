"""A YAML loader that reads times of day as strings.

PyYAML follows YAML 1.1, which reads ``13:30`` as the base 60 integer 810
and ``18:00:00`` as 64800. The config gives times of day in this form, for
example the range of `schedule`. YAML 1.2 dropped the base 60 numbers, and
this loader drops them too, so such a value stays a string.
"""

import re

import yaml

_INT = re.compile(
    r"""^(?:[-+]?0b[0-1_]+
    |[-+]?0[0-7_]+
    |[-+]?(?:0|[1-9][0-9_]*)
    |[-+]?0x[0-9a-fA-F_]+)$""",
    re.VERBOSE,
)
"""The YAML 1.1 int pattern of PyYAML without the base 60 form."""

_FLOAT = re.compile(
    r"""^(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+][0-9]+)?
    |\.[0-9][0-9_]*(?:[eE][-+][0-9]+)?
    |[-+]?\.(?:inf|Inf|INF)
    |\.(?:nan|NaN|NAN))$""",
    re.VERBOSE,
)
"""The YAML 1.1 float pattern of PyYAML without the base 60 form."""

_INT_TAG = "tag:yaml.org,2002:int"
_FLOAT_TAG = "tag:yaml.org,2002:float"


class GangwayLoader(yaml.SafeLoader):
    """A safe loader that reads base 60 numbers as strings.

    Use it as ``yaml.load(stream, Loader=GangwayLoader)``. It accepts the same
    documents as ``yaml.safe_load``. Only a value like ``13:30`` gives a
    string in place of a number.
    """


_BASE_60_FREE = (
    (_INT_TAG, _INT, "-+0123456789"),
    (_FLOAT_TAG, _FLOAT, "-+0123456789."),
)
"""The int and float resolvers with the characters that can start them."""

_KEPT = {
    first: [
        (tag, pattern)
        for tag, pattern in resolvers
        if tag not in (_INT_TAG, _FLOAT_TAG)
    ]
    for first, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}

# PyYAML tries the resolvers of a first character in list order, and
# add_implicit_resolver appends. The new patterns go last, as it would do.
GangwayLoader.yaml_implicit_resolvers = {
    first: _KEPT.get(first, [])
    + [(tag, pattern) for tag, pattern, firsts in _BASE_60_FREE if first in firsts]
    for first in _KEPT.keys() | {c for *_, firsts in _BASE_60_FREE for c in firsts}
}
