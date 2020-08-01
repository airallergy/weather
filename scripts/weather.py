import json
from pathlib import Path
import re
import pandas as pd
import numpy as np

from typing import Any, List, Tuple, Union
from os import PathLike

AnyPath = Union[str, bytes, PathLike]

with open("scripts/epw_scheme.json", "rt") as fh:
    EPW_SCHEME = json.load(fh)


class Epw:
    def __init__(self, epw_file: AnyPath) -> None:
        self.epw_file = Path(epw_file)
        self.headers = tuple(EPW_SCHEME.keys())
        self.header = self._convert_header(self.__class__.__name__, "var")

    def __getattr__(self, name: str) -> Any:
        if name in self.headers:
            header_cls_name = self._convert_header(name, "cls")
            instance = globals()[header_cls_name](self.epw_file)
            if name in ("comments_1", "comments_2"):
                return instance.metadata.loc[0, name]
            else:
                return instance
        elif ("metadata" in self.__dir__()) and (name in self.metadata.columns):
            return self.metadata.loc[0, name]
        elif ("data" in self.__dir__()) and (self.data is None):
            raise ValueError(
                "no '{}' data in '{}'".format(self.header, str(self.epw_file.resolve()))
            )
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
                tuple(item.lower() for item in re.findall("[A-Z0-9][^A-Z0-9]*", header))
            )

    def _check_header_sanity(self) -> None:
        if self.header == "epw":
            raise NotImplementedError
        elif self.header not in self.headers:
            raise ValueError("invalid header: {}".format(self.header))

    def _check_data_sanity(
        self, entry_data: List, fields: List[str], count: int
    ) -> None:
        if len(fields) * count != len(entry_data):
            raise ValueError(
                "data sanity check failed for '{}'".format(self.__class__.__name__)
            )

    def _read_scheme(self, category: str) -> Tuple[Union[List[str], str]]:
        self._check_header_sanity()
        fields = EPW_SCHEME[self.header][category]["fields"]
        types = EPW_SCHEME[self.header][category]["types"]
        if category == "data":
            count_idx = EPW_SCHEME[self.header][category]["count_idx"]
            return fields, types, count_idx
        else:
            return fields, types

    def _read_entry(self) -> Union[List[str], str]:
        self._check_header_sanity()
        start_ln_no = self.headers.index(self.header)
        with open(self.epw_file, "rt") as fh:
            epw = [line.rstrip() for line in fh.readlines()]
        if self.header == "records":
            return [item.split(",") for item in epw[start_ln_no:]]
        else:
            return epw[start_ln_no].split(",")[1:]

    def parse_metadata(self) -> pd.DataFrame:
        self._check_header_sanity()
        fields, types = self._read_scheme("metadata")
        entry = self._read_entry()
        if "data" in EPW_SCHEME[self.header].keys():
            self.entry_data = entry[len(fields) :]
        metadata = pd.DataFrame([entry[: len(fields)]], columns=fields)
        return metadata.astype(dict(zip(fields, types)))

    def parse_data(self) -> Union[pd.DataFrame, None]:
        self._check_header_sanity()
        fields, types, count_idx = self._read_scheme("data")
        count = getattr(self, count_idx)
        self._check_data_sanity(self.entry_data, fields, count)
        if not count:
            return None
        data = pd.DataFrame(
            (
                self.entry_data[i * len(fields) : (i + 1) * len(fields)]
                for i in range(count)
            ),
            columns=fields,
        )
        data.replace("", np.nan, inplace=True)
        return data.astype(dict(zip(fields, types)))


class Location(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()


class DesignConditions(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()

    def parse_data(self) -> pd.DataFrame:
        # TODO
        pass


class TypicalExtremePeriods(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()


class GroundTemperatures(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()


class HolidaysDaylightSaving(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()


class Comments1(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()


class Comments2(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()


class DataPeriods(Epw):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()


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
        return data.astype(dict(zip(fields, types)))


p = Path("scripts") / "in.epw"
w = Epw(p)
print(w.location.latitude)
print(w.design_conditions.number_of_design_conditions)
print(w.typical_extreme_periods.start_day)
print(w.ground_temperatures.depth)
print(w.holidays_daylight_saving.number_of_holidays)
print(w.comments_1)
print(w.comments_2)
print(w.data_periods.number_of_data_periods)
print(w.records.dry_bulb_temperature)
