from itertools import chain, islice
from dataclasses import dataclass, make_dataclass

from ._epw_schema import _EPW_SCHEMA, _EPW_HEADER_NAMES

from typing_extensions import Self  # from 3.11, see https://peps.python.org/pep-0673/
from typing import ClassVar, Iterator
from ._tools import AnyPath, AnyField, AnyRecords, AnyFieldSchema


"""Terminology
1. An epw weather file starts with several 'header records', followed by 'data records'.
"""

# TODO: check numbers
# TODO: rper
@dataclass(kw_only=True)
class _Records:
    def __getattr__(self, name: str):
        idx = next(
            (item[0] for item in enumerate(self.fields) if item[1][0] == name), None
        )
        if idx is None:
            raise AttributeError(f"invalid field name: '{name}'")
        return next(islice(zip(*self.records, strict=True), idx, None))

    @classmethod
    def _load_epw_records(cls, records_iter: Iterator[Iterator[str]]) -> AnyRecords:
        return tuple(
            zip(
                *(
                    map(field_type, field_vals)
                    for (_, field_type), field_vals in zip(
                        cls.fields, zip(*records_iter, strict=True), strict=True
                    )
                ),
                strict=True,
            )
        )

    def _dump_epw_records(self) -> Iterator[str]:
        return (",".join(map(str, record)) for record in self.records)


def _make_header_dataclass(header_name: str) -> type:
    header_name = header_name.lower()
    cls_name = "_" + "".join(item.capitalize() for item in header_name.split("_"))
    header_schema = _EPW_SCHEMA[header_name]
    metafields_schema = header_schema["metafields"]

    @dataclass(kw_only=True)
    class _Header(_Records):
        name: ClassVar[str] = header_name
        metafields: ClassVar[AnyFieldSchema] = metafields_schema

        @classmethod
        def _from_epw_line(cls, epw_line: str) -> Self:
            num_metafields = len(cls.metafields)
            epw_line_parts = tuple(epw_line.split(","))
            header_dict = {
                metafield_name: metafield_type(metafield_val)
                for (metafield_name, metafield_type), metafield_val in zip(
                    cls.metafields,
                    epw_line_parts[1 : num_metafields + 1],
                    strict=True,
                )
            }
            if "fields" in cls.__dict__:
                records_1d = epw_line_parts[num_metafields + 1 :]
                header_dict["records"] = (
                    cls._load_epw_records(records_1d) if len(records_1d) > 0 else ()
                )
            return cls._from_dict(header_dict)

        @classmethod
        def _from_dict(cls, header_dict: dict[str : AnyField | AnyRecords]) -> Self:
            return cls(**header_dict)

        def _to_epw_line(self) -> str:
            return (
                _EPW_HEADER_NAMES[header_name]
                + ","
                + ",".join(
                    map(str, (self.__dict__[item] for item, _ in self.metafields))
                )
                + (
                    "," + self._dump_epw_records()
                    if "fields" in self.__class__.__dict__
                    else ""
                )
            )

        @classmethod
        def _load_epw_records(cls, epw_records: tuple[str]) -> AnyRecords:
            ## temporary for design conditions ##
            if cls.name == "design_conditions":
                return ",".join(epw_records)
            #####################################
            return super()._load_epw_records(
                zip(
                    *(
                        (iter(item if item != "" else "nan" for item in epw_records),)
                        * len(cls.fields)
                    ),
                    strict=True,
                )
            )

        def _dump_epw_records(self) -> str:
            ## temporary for design conditions ##
            if self.name == "design_conditions":
                return self.records
            #####################################
            return ",".join(super()._dump_epw_records()).replace("nan", "")

    records_schema = (("records", AnyRecords),) if "fields" in header_schema else ()
    namespace = {"fields": header_schema["fields"]} if "fields" in header_schema else {}

    return make_dataclass(
        cls_name,
        chain(metafields_schema, records_schema),
        bases=(_Header,),
        namespace=namespace,
        kw_only=True,
    )


_Location = _make_header_dataclass("location")
_DesignConditions = _make_header_dataclass("design_conditions")
_TypicalExtremePeriods = _make_header_dataclass("typical_extreme_periods")
_GroundTemperatures = _make_header_dataclass("ground_temperatures")
_HolidaysDaylightSaving = _make_header_dataclass("holidays_daylight_saving")
_Comments1 = _make_header_dataclass("comments_1")
_Comments2 = _make_header_dataclass("comments_2")
_DataPeriods = _make_header_dataclass("data_periods")


@dataclass(kw_only=True)
class EPW(_Records):
    location: _Location
    design_conditions: _DesignConditions
    typical_extreme_periods: _TypicalExtremePeriods
    ground_temperatures: _GroundTemperatures
    holidays_daylight_saving: _HolidaysDaylightSaving
    comments_1: _Comments1
    comments_2: _Comments2
    data_periods: _DataPeriods
    records: AnyRecords
    fields: ClassVar[AnyFieldSchema] = _EPW_SCHEMA["data"]["fields"]

    @classmethod
    def from_epw(cls, epw_file: AnyPath) -> Self:
        with open(epw_file, "rt") as fp:
            epw_iter = (line.rstrip() for line in fp.readlines())

        return cls(
            location=_Location._from_epw_line(next(epw_iter)),
            design_conditions=_DesignConditions._from_epw_line(next(epw_iter)),
            typical_extreme_periods=_TypicalExtremePeriods._from_epw_line(
                next(epw_iter)
            ),
            ground_temperatures=_GroundTemperatures._from_epw_line(next(epw_iter)),
            holidays_daylight_saving=_HolidaysDaylightSaving._from_epw_line(
                next(epw_iter)
            ),
            comments_1=_Comments1._from_epw_line(next(epw_iter)),
            comments_2=_Comments2._from_epw_line(next(epw_iter)),
            data_periods=_DataPeriods._from_epw_line(next(epw_iter)),
            records=cls._load_epw_records(epw_iter),
        )

    def to_epw(self, epw_file: AnyPath) -> None:
        with open(epw_file, "wt") as fp:
            fp.write(
                "\n".join(
                    (
                        self.location._to_epw_line(),
                        self.design_conditions._to_epw_line(),
                        self.typical_extreme_periods._to_epw_line(),
                        self.ground_temperatures._to_epw_line(),
                        self.holidays_daylight_saving._to_epw_line(),
                        self.comments_1._to_epw_line(),
                        self.comments_2._to_epw_line(),
                        self.data_periods._to_epw_line(),
                        *self._dump_epw_records(),
                    )
                )
                + "\n"
            )

    @classmethod
    def _load_epw_records(cls, epw_records: Iterator[str]) -> AnyRecords:
        return super()._load_epw_records(
            (iter(epw_record.split(",")) for epw_record in epw_records)
        )
