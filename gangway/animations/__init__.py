"""Animation functions for the LED strips.

Each function in `__all__` of the `idle`, `responsive` and `meta` packages
is an animation factory. Each package holds one animation per module, or a
small group of similar ones. The animation config calls a factory by its
name. The factory returns a `gangway.types.Animation`.
"""
