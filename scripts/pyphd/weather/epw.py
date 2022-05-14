import sys
from itertools import chain, islice
from dataclasses import dataclass, make_dataclass

from ._tools import records_tuple
from ._epw_schema import _EPW_SCHEMA, _EPW_HEADER_NAMES

from typing_extensions import Self  # from 3.11, see https://peps.python.org/pep-0673/
from typing import ClassVar, Iterator
from ._tools import AnyPath, AnyField, AnyRecords, AnyFieldSchema


"""Terminology
1. An epw weather file starts with several 'header records', followed by 'data records'.
"""

# TODO: check numbers
# TODO: rper
DATACLASS_PARAMS = {
    "repr": False,
    "eq": False,  # not work for float("nan")
    "order": False,  # see 'eq'
    "kw_only": True,
    "slots": True,  # explicit super(), see https://bugs.python.org/issue46404, https://stackoverflow.com/a/1817840
}


@dataclass(**DATACLASS_PARAMS)
class _Records:
    def __repr__(self):
        metafield_names = chain(
            self.metafields.keys(),
            ("records",) if "fields" in self.__class__.__dict__ else (),
        )
        return f"<{self.__class__.__name__}: {', '.join(metafield_name for metafield_name in metafield_names)}>"

    def __getattr__(self, name: str):
        idx = next(
            (
                idx
                for idx, field_name in enumerate(self.fields.keys())
                if field_name == name
            ),
            None,
        )
        if idx is None:
            raise AttributeError(f"invalid field name: '{name}'")
        return next(islice(zip(*self.records, strict=True), idx, None))

    @classmethod
    def _load_epw_records(cls, records_iter: Iterator[Iterator[str]]) -> AnyRecords:
        return type(sys.intern(f"{cls.name}_records"), (records_tuple,), {})(
            zip(
                *(
                    map(field_type, field_vals)
                    for field_type, field_vals in zip(
                        cls.fields.values(),
                        zip(*records_iter, strict=True),
                        strict=True,
                    )
                ),
                strict=True,
            ),
            field_names=cls.fields.keys(),
        )

    def _dump_epw_records(self) -> Iterator[str]:
        return (",".join(map(str, record)) for record in self.records)


@dataclass(**DATACLASS_PARAMS)
class _Header(_Records):
    @classmethod
    def _from_epw_line(cls, epw_line: str) -> Self:
        num_metafields = len(cls.metafields)
        epw_line_parts = tuple(epw_line.split(","))
        header_dict = {
            metafield_name: metafield_type(metafield_val)
            for (metafield_name, metafield_type), metafield_val in zip(
                cls.metafields.items(),
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
        return ",".join(
            chain(
                (_EPW_HEADER_NAMES[self.name],),
                map(
                    str,
                    (
                        getattr(self, metafield_name)
                        for metafield_name in self.metafields.keys()
                    ),
                ),
                (
                    (self._dump_epw_records(),)
                    if "fields" in self.__class__.__dict__
                    else ()
                ),
            )
        )

    @classmethod
    def _load_epw_records(cls, epw_records: tuple[str]) -> AnyRecords:
        ## temporary for design conditions ##
        if cls.name == "design_conditions":
            return ",".join(epw_records)
        #####################################
        return super(_Header, cls)._load_epw_records(
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
        return ",".join(super(_Header, self)._dump_epw_records()).replace("nan", "")


def _make_header_dataclass(header_name: str) -> type:
    header_name = header_name.lower()
    cls_name = "_" + "".join(item.capitalize() for item in header_name.split("_"))
    header_schema = _EPW_SCHEMA[header_name]
    metafields_schema = header_schema["metafields"]

    records_schema, namespace = (
        (
            {"records": AnyRecords},
            {
                "name": header_name,
                "metafields": metafields_schema,
                "fields": header_schema["fields"],
            },
        )
        if "fields" in header_schema
        else (
            {},
            {"name": header_name, "metafields": metafields_schema},
        )
    )

    return make_dataclass(
        cls_name,
        chain(metafields_schema.items(), records_schema.items()),
        bases=(_Header,),
        namespace=namespace,
        **DATACLASS_PARAMS,
    )


_Location = _make_header_dataclass("location")
_DesignConditions = _make_header_dataclass("design_conditions")
_TypicalExtremePeriods = _make_header_dataclass("typical_extreme_periods")
_GroundTemperatures = _make_header_dataclass("ground_temperatures")
_HolidaysDaylightSaving = _make_header_dataclass("holidays_daylight_saving")
_Comments1 = _make_header_dataclass("comments_1")
_Comments2 = _make_header_dataclass("comments_2")
_DataPeriods = _make_header_dataclass("data_periods")


@dataclass(**DATACLASS_PARAMS)
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
    name: ClassVar[str] = "epw"
    metafields: ClassVar[AnyFieldSchema] = {
        "location": _Location,
        "design_conditions": _DesignConditions,
        "typical_extreme_periods": _TypicalExtremePeriods,
        "ground_temperatures": _GroundTemperatures,
        "holidays_daylight_saving": _HolidaysDaylightSaving,
        "comments_1": _Comments1,
        "comments_2": _Comments2,
        "data_periods": _DataPeriods,
    }
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
        return super(EPW, cls)._load_epw_records(
            (iter(epw_record.split(",")) for epw_record in epw_records)
        )
