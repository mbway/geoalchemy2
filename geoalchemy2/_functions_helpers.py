from textwrap import TextWrapper
from typing import Optional
from typing import Tuple
from typing import Union


def _get_docstring(name: str, doc: Union[None, str, Tuple[str, str]], type_: Optional[type]) -> str:
    doc_string_parts = []

    wrapper = TextWrapper(width=100)

    if isinstance(doc, tuple):
        doc_string_parts.append("\n".join(wrapper.wrap(doc[0])))
        doc_string_parts.append("see https://postgis.net/docs/{0}.html".format(doc[1]))
    elif doc is not None:
        doc_string_parts.append("\n".join(wrapper.wrap(doc)))
        doc_string_parts.append("see https://postgis.net/docs/{0}.html".format(name))

    if type_ is not None:
        return_type_str = "{0}.{1}".format(type_.__module__, type_.__name__)
        doc_string_parts.append("Return type: :class:`{0}`.".format(return_type_str))

    return "\n\n".join(doc_string_parts)


def _replace_indent(text: str, indent: str) -> str:
    lines = []
    for i, line in enumerate(text.splitlines()):
        if i == 0 or not line.strip():
            lines.append(line)
        else:
            lines.append(f"{indent}{line}")
    return "\n".join(lines)


def _generate_stubs() -> str:
    """Generates type stubs for the dynamic functions described in `geoalchemy2/_functions.py`."""
    from geoalchemy2._functions import _FUNCTIONS
    from geoalchemy2.functions import ST_AsGeoJSON

    header = '''\
# this file is automatically generated
from typing import Any
from typing import List

from sqlalchemy.sql import functions
from sqlalchemy.sql.elements import ColumnElement

import geoalchemy2.types

class GenericFunction(functions.GenericFunction): ...

class TableRowElement(ColumnElement):
    inherit_cache: bool = ...
    """The cache is disabled for this class."""

    def __init__(self, selectable: bool) -> None: ...
    @property
    def _from_objects(self) -> List[bool]: ...  # type: ignore[override]
'''
    stub_file_parts = [header]

    functions = _FUNCTIONS.copy()
    functions.insert(0, ("ST_AsGeoJSON", str, ST_AsGeoJSON.__doc__))

    for name, type_, doc_parts in functions:
        doc = _replace_indent(_get_docstring(name, doc_parts, type_), "    ")

        if type_ is None:
            type_str = "Any"
        elif type_.__module__ == "builtins":
            type_str = type_.__name__
        else:
            type_str = f"{type_.__module__}.{type_.__name__}"

        signature = f'''\
class _{name}(functions.GenericFunction):
    """
    {doc}
    """

    def __call__(self, *args: Any, **kwargs: Any) -> {type_str}: ...

{name}: _{name}
'''
        stub_file_parts.append(signature)

    return "\n".join(stub_file_parts)
