import json
from pathlib import Path
import re
import pandas as pd

from typing import List, Union
from os import PathLike

AnyPath = Union[str, bytes, PathLike]

with open("scripts/epw_scheme.json", "rt") as fh:
    EPW_SCHEME = json.load(fh)


class Epw:
    def __init__(self, epw_file: AnyPath) -> None:
        self.epw_file = epw_file

    def __getattr__(self, name: str) -> object:
        if name in EPW_SCHEME.keys():
            header_cls_name = self._convert_header(name, "cls")
            return globals()[header_cls_name](self.epw_file)
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

    def get_record(self, header: str) -> Union[List[str], str]:
        header = header.lower()

        headers = tuple(EPW_SCHEME.keys())
        if header not in headers:
            raise ValueError("invalid header")
        start_ln_no = headers.index(header)
        with open(self.epw_file, "rt") as fh:
            epw = [line.rstrip() for line in fh.readlines()]
        if header == headers[-1]:
            record = epw[start_ln_no:]
        else:
            record = epw[start_ln_no].split(header + ",")[-1].strip()
        return record


# class GroundTemperature(Epw):
#     def get_val(self, )


class Data(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.header = self._convert_header(self.__class__.__name__, "var")
        self.all = self.parse_val()

    def __getattr__(self, name: str) -> List:
        if name in self.fields:
            return self.all[name]
        else:
            raise AttributeError(
                "'{}' object has no attribute '{}'".format(
                    self.__class__.__name__, name
                )
            )

    def parse_val(self) -> pd.DataFrame:
        record = self.get_record(self.header)
        data = pd.DataFrame(item.split(",") for item in record)
        fields = EPW_SCHEME[self.header]["fields"][: data.shape[1]]
        types = EPW_SCHEME[self.header]["types"][: data.shape[1]]
        data.columns = fields
        data = data.astype(dict(zip(fields, types)))
        data.hour -= 1
        timestamp = data.apply(
            lambda x: pd.Timestamp(year=x.year, month=x.month, day=x.day, hour=x.hour),
            axis=1,
        )
        data.index = pd.DatetimeIndex(timestamp)
        data = data.drop(columns=["year", "month", "day", "hour", "minute"])
        self.fields = data.columns
        return data


p = Path("scripts") / "in.epw"
# a = Data(p)
w = Epw(p)
# b = tuple(EPW_SCHEME.keys())
print(w.data.dry_bulb_temperature)
