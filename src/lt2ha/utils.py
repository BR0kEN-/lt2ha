from typing import Any


def build_topic(prefix: str, kind: str, op: str) -> str:
    return f"{prefix}/{kind}/{op}" if kind else f"{prefix}/{op}"


def get_generic_args(cls: type, generic_position: int = 0) -> tuple[Any, ...]:
    # The `__orig_bases__` is introduced since 3.7 in PEP-560.
    # See https://peps.python.org/pep-0560/
    #
    # The `[generic_position]` here is the `Generic`
    # that has a `[arg_position]` argument.
    #
    # noinspection PyUnresolvedReferences
    return cls.__orig_bases__[generic_position].__args__


def to_id(string: str) -> str:
    return (
        string
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace(":", "_")
    )


__all__ = [
    "build_topic",
    "get_generic_args",
    "to_id",
]
