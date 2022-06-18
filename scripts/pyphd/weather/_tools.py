import sys
import pandas as pd

from os import PathLike

AnyStrPath = str | PathLike[str]
AnyFieldSchema = dict[str, type]
AnyField = int | float | str
AnyRecords = tuple[tuple[AnyField, ...], ...]  # NOTE: the 1st tuple refers to rectuple

rectuple = lambda type_name, field_names: type(
    sys.intern(type_name),
    (tuple,),
    {
        "to_pandas": lambda self: pd.DataFrame(self, columns=self.field_names),
        "__str__": lambda self: tuple(self).__str__(),  # return a tuple-like string
        "__repr__": lambda self: self.to_pandas().__repr__(),  # return a pandas-like representation
        "_repr_html_": lambda self: self.to_pandas()._repr_html_(),  # return a pandas-like representation in Jupyter Notebook
        # "__getnewargs__": lambda self: tuple(self),  # used by copy and pickle
        "field_names": field_names,
        # "__match_args__": field_names,
        # "__module__": sys._getframe(1).f_globals.get(
        #     "__name__", "__main__"
        # ),  # used by pickle
    },
)
