"""The `YamlValue` type."""

type YamlValue = (
    str | int | float | bool | None | list[YamlValue] | dict[str, YamlValue]
)
"""A value that ``yaml.safe_load`` can return for a plain YAML document."""
