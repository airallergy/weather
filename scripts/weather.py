import json
from pathlib import Path
import re
import pandas as pd
import numpy as np

from typing import List, Tuple, Union
from os import PathLike

AnyPath = Union[str, bytes, PathLike]

with open("scripts/epw_scheme.json", "rt") as fh:
    EPW_SCHEME = json.load(fh)


class Epw:
    def __init__(self, epw_file: AnyPath) -> None:
        self.epw_file = epw_file
        self.headers = tuple(EPW_SCHEME.keys())
        self.header = self._convert_header(self.__class__.__name__, "var")

    def __getattr__(self, name: str) -> object:
        if name in self.headers:

            header_cls_name = self._convert_header(name, "cls")
            return globals()[header_cls_name](self.epw_file)
        elif ("metadata" in self.__dir__()) and (name in self.metadata.columns):
            return self.metadata.loc[0, name]
        elif ("data" in self.__dir__()) and (name in self.data.columns):
            return self.data[name]
        else:
            raise AttributeError(
                "'{}' object has no attribute '{}'".format(
                    self.__class__.__name__, name
                )
            )

    @staticmethod
    def _convert_header(header: str, to: str) -> str:
        if to == "cls":
            return "".join(tuple(item.capitalize() for item in header.split("_")))
        elif to == "var":
            return "_".join(
                tuple(item.lower() for item in re.findall("[A-Z][^A-Z]*", header))
            )

    def _check_sanity(self, entry_data: List, fields: List[str], count: int) -> None:
        if len(fields) * count != len(entry_data):
            raise ValueError(
                "sanity check failed for {}".format(self.__class__.__name__)
            )

    def _read_scheme(self, category: str) -> Tuple[Union[List[str], str]]:
        fields = EPW_SCHEME[self.header][category]["fields"]
        types = EPW_SCHEME[self.header][category]["types"]
        if category == "data":
            count_idx = EPW_SCHEME[self.header][category]["count_idx"]
            return fields, types, count_idx
        else:
            return fields, types

    def _read_entry(self) -> Union[List[str], str]:
        if self.header not in self.headers:
            raise ValueError("invalid header: {}".format(self.header))
        start_ln_no = self.headers.index(self.header)
        with open(self.epw_file, "rt") as fh:
            epw = [line.rstrip() for line in fh.readlines()]
        if self.header == "records":
            return [item.split(",") for item in epw[start_ln_no:]]
        else:
            return epw[start_ln_no].split(",")[1:]


class GroundTemperatures(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()

    def parse_metadata(self) -> pd.DataFrame:
        fields, types = self._read_scheme("metadata")
        entry = self._read_entry()
        metadata = pd.DataFrame(dict(zip(fields, entry[: len(fields)])), index=[0])
        metadata = metadata.astype(dict(zip(fields, types)))
        self.entry_data = entry[len(fields) :]
        return metadata

    def parse_data(self) -> pd.DataFrame:
        fields, types, count_idx = self._read_scheme("data")
        count = getattr(self, count_idx)
        self._check_sanity(self.entry_data, fields, count)
        data = pd.DataFrame(
            self.entry_data[i * len(fields) : (i + 1) * len(fields)]
            for i in range(count)
        )
        data.replace("", np.nan, inplace=True)
        data.columns = fields
        data = data.astype(dict(zip(fields, types)))
        return data


class Records(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.data = self.parse_data()

    def parse_data(self) -> pd.DataFrame:
        fields, types, _ = self._read_scheme("data")
        entry = self._read_entry()
        data = pd.DataFrame(entry)
        data.replace("", np.nan, inplace=True)
        num_col = data.shape[1]
        fields = fields[:num_col]
        types = types[:num_col]
        data.columns = fields
        data = data.astype(dict(zip(fields, types)))
        timestamp = data.apply(
            lambda x: pd.Timestamp(
                year=x.year,
                month=x.month,
                day=x.day,
                hour=x.hour - 1,
                minute=int(x.minute / 2),
            ),
            axis=1,
        )
        data.index = pd.DatetimeIndex(timestamp)
        data = data.drop(columns=["year", "month", "day", "hour", "minute"])
        return data


p = Path("scripts") / "in.epw"
w = Epw(p)
print(w.records.dry_bulb_temperature)
print(w.ground_temperatures.ground_temperature_depth)
