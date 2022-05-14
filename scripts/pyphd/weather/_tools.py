# import sys
import numpy as np
import pandas as pd

from os import PathLike
from typing import Iterable

AnyPath = str | bytes | PathLike[str] | PathLike[bytes]
AnyFieldSchema = dict[str:type]
AnyField = int | float | str
AnyRecords = tuple[tuple[AnyField]]


class records_tuple(tuple):
    """modified from 'collections.namedtuple'."""

    # __match_args__ = None
    # # for pickling to work, the __module__ variable needs to be set to the frame where the named tuple is created.
    # __module__ = sys._getframe(1).f_globals.get("__name__", "__main__")
    field_names = None

    def __new__(cls, records_iter: Iterable[Iterable[AnyField]], *, field_names):
        cls.field_names = tuple(field_names)
        # cls.__match_args__ = cls.field_names
        return super().__new__(cls, records_iter)

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
        return pd.DataFrame(self, columns=self.field_names)._repr_html_()

    def __str__(self):
        """return a tuple-like string."""
        return tuple(self).__str__()

    # def __getnewargs__(self):
    #     """return self as a plain tuple.  Used by copy and pickle."""
    #     return tuple(self)
