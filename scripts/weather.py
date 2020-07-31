import json
from pathlib import Path
import re
import pandas as pd
import numpy as np

from typing import List, Union
from os import PathLike

AnyPath = Union[str, bytes, PathLike]

with open("scripts/epw_scheme.json", "rt") as fh:
    EPW_SCHEME = json.load(fh)


class Epw:
    def __init__(self, epw_file: AnyPath) -> None:
        self.epw_file = epw_file
        self.header = self._convert_header(self.__class__.__name__, "var")

    def __getattr__(self, name: str) -> object:
        if name in EPW_SCHEME.keys():

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

    def read_entry(self, header: str) -> Union[List[str], str]:
        header = header.lower()
        headers = tuple(EPW_SCHEME.keys())
        if header not in headers:
            raise ValueError("invalid header")
        start_ln_no = headers.index(header)
        with open(self.epw_file, "rt") as fh:
            epw = [line.rstrip() for line in fh.readlines()]
        if header == headers[-1]:
            entry = epw[start_ln_no:]
        else:
            entry = epw[start_ln_no].split(header + ",")[-1].strip()
        return entry


class GroundTemperatures(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()

    def parse_metadata(self):
        fields = EPW_SCHEME[self.header]["metadata"]["fields"]
        types = EPW_SCHEME[self.header]["metadata"]["types"]
        entry = self.read_entry(self.header)
        entry = entry.split(",")[1:]
        metadata = pd.DataFrame(dict(zip(fields, entry[: len(fields)])), index=[0])
        metadata = metadata.astype(dict(zip(fields, types)))
        self.entry_data = entry[len(fields) :]
        return metadata

    def parse_data(self):
        fields = EPW_SCHEME[self.header]["data"]["fields"]
        types = EPW_SCHEME[self.header]["data"]["types"]
        count_idx = EPW_SCHEME[self.header]["data"]["count"]
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
        entry = self.read_entry(self.header)
        data = pd.DataFrame(item.split(",") for item in entry)
        data.replace("", np.nan, inplace=True)
        fields = EPW_SCHEME[self.header]["fields"][: data.shape[1]]
        types = EPW_SCHEME[self.header]["types"][: data.shape[1]]
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
# b = tuple(EPW_SCHEME.keys())
# print(w.records.dry_bulb_temperature)
print(w.ground_temperatures.soil_conductivity)
