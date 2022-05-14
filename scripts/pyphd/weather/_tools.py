import sys
import numpy as np
import pandas as pd

from os import PathLike
from typing import Iterable

AnyPath = str | bytes | PathLike[str] | PathLike[bytes]
AnyFieldSchema = dict[str:type]
AnyField = int | float | str
AnyRecords = tuple[tuple[AnyField]]


def records_tuple(type_name, field_names):
    def __str__(self):
        """return a tuple-like string."""
        return tuple(self).__str__()

    def __repr__(self):
        """return a numpy-like representation without Jupyter Notebook."""
        return (
            (prefix := f"{self.__class__.__name__}[")
            + np.array2string(
                np.array(self), separator=", ", prefix=prefix, suffix="]"
            ).translate(str.maketrans("[]", "()"))
            + "]"
        )

    def _repr_html_(self) -> str | None:
        """return a pandas-like representation with Jupyter Notebook."""
        return pd.DataFrame(
            self,
            columns=(
                field_name.replace("_", " ").capitalize()
                for field_name in self.field_names
            ),
        )._repr_html_()

    # def __getnewargs__(self):
    #     """return self as a plain tuple.  Used by copy and pickle."""
    #     return tuple(self)

    return type(
        sys.intern(type_name),
        (tuple,),
        {
            "__str__": __str__,
            "__repr__": __repr__,
            "_repr_html_": _repr_html_,
            # "__getnewargs__": __getnewargs__,
            "field_names": field_names,
            # "__match_args__": field_names,
            # "__module__": sys._getframe(1).f_globals.get("__name__", "__main__"),
        },
    )
