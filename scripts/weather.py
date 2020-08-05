import json
from pathlib import Path
import numpy as np
import re

from typing import Any, Iterable, List, Tuple, Union
from os import PathLike

AnyPath = Union[str, bytes, PathLike]

with open("scripts/epw_scheme.json", "rt") as fh:
    EPW_SCHEME = json.load(fh)


class Epw:
    def __init__(self, epw_file: AnyPath) -> None:
        self.epw_file = Path(epw_file)
        self.headers = tuple(EPW_SCHEME.keys())
        self.header = self._convert_header(self.__class__.__name__, "var")
        if self.header in self.headers:
            self.fields = []

    def __getattr__(self, name: str) -> Any:
        if name in self.headers:
            header_cls_name = self._convert_header(name, "cls")
            instance = globals()[header_cls_name](self.epw_file)
            if name in ("comments_1", "comments_2"):
                return instance.metadata[name].item()
            else:
                return instance
        elif ("metadata" in self.__dir__()) and (name in self.metadata.dtype.names):
            return self.metadata[name].item()
        elif ("data" in self.__dir__()) and (self.data is None):
            raise ValueError(f"no '{self.header}' data in '{self.epw_file.resolve()}'")
        elif ("data" in self.__dir__()) and (name in self.data.dtype.names):
            return self.data[name]
        else:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )

    def __dir__(self) -> List[str]:
        if self.header == "epw":
            return sorted(
                set(super().__dir__() + list(self.__dict__.keys()) + list(self.headers))
            )
        elif self.header in self.headers:
            return sorted(
                set(super().__dir__() + list(self.__dict__.keys()) + list(self.fields))
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
            raise ValueError(f"invalid header: {self.header}")

    def _check_data_sanity(
        self, entry_data: Iterable, fields: Iterable[str], count: int
    ) -> None:
        if len(fields) * count != len(entry_data):
            raise ValueError(
                f"data sanity check failed for '{self.__class__.__name__}'"
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

    def parse_metadata(self) -> np.ndarray:
        self._check_header_sanity()
        fields, types = self._read_scheme("metadata")
        self.fields.extend(fields)
        entry = self._read_entry()
        entry_metadata = tuple(
            np.nan if item.strip() == "" else item for item in entry[: len(fields)]
        )
        if "data" in EPW_SCHEME[self.header].keys():
            self.entry_data = entry[len(fields) :]
        return np.array(entry_metadata, dtype=list(zip(fields, types)))

    def parse_data(self) -> Union[np.ndarray, None]:
        self._check_header_sanity()
        fields, types, count_idx = self._read_scheme("data")
        self.fields.extend(fields)
        count = getattr(self, count_idx)
        self._check_data_sanity(self.entry_data, fields, count)
        if not count:
            return None
        entry_data = tuple(
            np.nan if item.strip() == "" else item for item in self.entry_data
        )
        return np.array(
            [entry_data[i * len(fields) : (i + 1) * len(fields)] for i in range(count)],
            dtype=list(zip(fields, types)),
        )


class Location(Epw):
    def __init__(self, epw_file: AnyPath) -> None:
        super().__init__(epw_file)
        self.metadata = self.parse_metadata()
        self.fields.extend("state_province_region".split("_"))

    def __getattr__(self, name: str) -> Any:
        if name in "state_province_region".split("_"):
            return self.metadata["state_province_region"].item()
        else:
            return super().__getattr__(name)


class DesignConditions(Epw):
    def __init__(self, epw_file: AnyPath) -> None:
        super().__init__(epw_file)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()

    def parse_data(self) -> np.ndarray:
        # TODO
        pass


class TypicalExtremePeriods(Epw):
    def __init__(self, epw_file: AnyPath) -> None:
        super().__init__(epw_file)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()


class GroundTemperatures(Epw):
    def __init__(self, epw_file: AnyPath) -> None:
        super().__init__(epw_file)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()


class HolidaysDaylightSaving(Epw):
    def __init__(self, epw_file: AnyPath) -> None:
        super().__init__(epw_file)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()


class Comments1(Epw):
    def __init__(self, epw_file: AnyPath) -> None:
        super().__init__(epw_file)
        self.metadata = self.parse_metadata()


class Comments2(Epw):
    def __init__(self, epw_file: AnyPath) -> None:
        super().__init__(epw_file)
        self.metadata = self.parse_metadata()


class DataPeriods(Epw):
    def __init__(self, epw_file: AnyPath) -> None:
        super().__init__(epw_file)
        self.metadata = self.parse_metadata()
        self.data = self.parse_data()


class Records(Epw):
    def __init__(self, epw_file: AnyPath) -> None:
        super().__init__(epw_file)
        self.data = self.parse_data()

    def parse_data(self) -> np.ndarray:
        self._check_header_sanity()
        fields, types, _ = self._read_scheme("data")
        self.fields.extend(fields)
        entry_data = [
            tuple(np.nan if item.strip() == "" else item for item in arr)
            for arr in self._read_entry()
        ]
        num_fields = len(entry_data[0])
        fields = fields[:num_fields]
        types = types[:num_fields]
        return np.array(entry_data, dtype=list(zip(fields, types)))


if __name__ == "__main__":
    p = Path("scripts") / "in.epw"
    w = Epw(p)
    print(w.location.region)
    print(w.design_conditions.number_of_design_conditions)
    print(w.typical_extreme_periods.start_day)
    print(w.ground_temperatures.depth)
    print(w.holidays_daylight_saving.number_of_holidays)
    print(w.comments_1)
    print(w.comments_2)
    print(w.data_periods.number_of_data_periods)
    print(w.records.dry_bulb_temperature)
    print(dir(w))
    print(dir(w.location))
    # print(w.haha)
    # print(w.location.haha)
