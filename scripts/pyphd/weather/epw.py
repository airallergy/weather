from itertools import chain, islice
from dataclasses import dataclass, make_dataclass

from ._tools import rectuple
from ._epw_schema import _EPW_SCHEMA, _EPW_HEADER_NAMES

from typing import ClassVar
from typing_extensions import Self  # from 3.11, see https://peps.python.org/pep-0673/
from collections.abc import Iterator, Iterable
from ._tools import AnyStrPath, AnyField, AnyRecords, AnyFieldSchema


"""Terminology
1. An epw weather file starts with several 'header records', followed by 'data records'.
"""

# TODO: check numbers

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
        if not (
            ("fields" in self.__class__.__dict__)
            and (name in (field_names_view := self.fields.keys()))
        ):
            raise AttributeError(f"{name} is no valid field of '{self.name}'.")

        if self.records == ():
            return ()

        idx = next(
            (
                idx
                for idx, field_name in enumerate(field_names_view)
                if field_name == name
            ),
            None,
        )
        if idx is None:
            raise AttributeError(f"invalid field name: '{name}'")
        return next(islice(zip(*self.records, strict=True), idx, None))

    @classmethod
    def _load_epw_records_generic(
        cls, records_iter: Iterator[Iterable[str]]
    ) -> AnyRecords:
        return rectuple(f"{cls.name}_records", cls.fields.keys())(
            zip(
                *(
                    tuple(  # NOTE: this tuple cannot be omited somehow
                        field_type("nan")
                        if ((field_val == "") and (field_type == float))
                        else field_type(field_val)
                        for field_val in field_vals
                    )
                    for field_type, field_vals in zip(
                        cls.fields.values(),
                        zip(*records_iter, strict=True),
                        strict=True,
                    )
                ),
                strict=True,
            )
        )

    def _dump_epw_records_generic(self) -> Iterator[str]:
        return (
            ",".join(map(str, record)).replace("nan", "") for record in self.records
        )


@dataclass(**DATACLASS_PARAMS)
class _Header(_Records):
    @classmethod
    def _from_epw_line(cls, epw_line: str) -> Self:  # type: ignore[valid-type] # python/mypy#11666
        num_metafields = len(cls.metafields)
        epw_line_parts = tuple(
            epw_line.split(",", (1 if cls.name.startswith("comments_") else -1))
        )
        metadata = epw_line_parts[1 : num_metafields + 1]
        header_dict = {
            metafield_name: metafield_type(metafield_val)
            for (metafield_name, metafield_type), metafield_val in zip(
                cls.metafields.items(),
                metadata + ("",) * (len(cls.metafields) - len(metadata)),  # for bad epw
                strict=True,
            )
        }
        if "fields" in cls.__dict__:
            records_1d = epw_line_parts[num_metafields + 1 :]
            header_dict["records"] = cls._load_epw_records(records_1d)
        return cls._from_dict(header_dict)

    @classmethod
    def _from_dict(cls, header_dict: dict[str, AnyField | AnyRecords]) -> Self:  # type: ignore[valid-type] # python/mypy#11666
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
    def _load_epw_records(cls, epw_records: tuple[str, ...]) -> AnyRecords:
        ## temporary for design conditions ##
        if cls.name == "design_conditions":
            return ",".join(epw_records)
        #####################################
        if len(epw_records) == 0:
            return ()
        return cls._load_epw_records_generic(
            zip(*((iter(epw_records),) * len(cls.fields)), strict=True)
        )

    def _dump_epw_records(self) -> str:
        ## temporary for design conditions ##
        if self.name == "design_conditions":
            return self.records
        #####################################
        return ",".join(self._dump_epw_records_generic())


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
    location: _Location  # type: ignore[valid-type] # python/mypy#6063
    design_conditions: _DesignConditions  # type: ignore[valid-type] # python/mypy#6063
    typical_extreme_periods: _TypicalExtremePeriods  # type: ignore[valid-type] # python/mypy#6063
    ground_temperatures: _GroundTemperatures  # type: ignore[valid-type] # python/mypy#6063
    holidays_daylight_saving: _HolidaysDaylightSaving  # type: ignore[valid-type] # python/mypy#6063
    comments_1: _Comments1  # type: ignore[valid-type] # python/mypy#6063
    comments_2: _Comments2  # type: ignore[valid-type] # python/mypy#6063
    data_periods: _DataPeriods  # type: ignore[valid-type] # python/mypy#6063
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
    def from_epw(cls, epw_file: AnyStrPath) -> Self:  # type: ignore[valid-type] # python/mypy#11666
        with open(epw_file, "rt") as fp:
            epw_iter = (line.rstrip() for line in fp.readlines())

        return cls(
            location=_Location._from_epw_line(next(epw_iter)),  # type: ignore[attr-defined] # python/mypy#6063
            design_conditions=_DesignConditions._from_epw_line(next(epw_iter)),  # type: ignore[attr-defined] # python/mypy#6063
            typical_extreme_periods=_TypicalExtremePeriods._from_epw_line(  # type: ignore[attr-defined] # python/mypy#6063
                next(epw_iter)
            ),
            ground_temperatures=_GroundTemperatures._from_epw_line(next(epw_iter)),  # type: ignore[attr-defined] # python/mypy#6063
            holidays_daylight_saving=_HolidaysDaylightSaving._from_epw_line(  # type: ignore[attr-defined] # python/mypy#6063
                next(epw_iter)
            ),
            comments_1=_Comments1._from_epw_line(next(epw_iter)),  # type: ignore[attr-defined] # python/mypy#6063
            comments_2=_Comments2._from_epw_line(next(epw_iter)),  # type: ignore[attr-defined] # python/mypy#6063
            data_periods=_DataPeriods._from_epw_line(next(epw_iter)),  # type: ignore[attr-defined] # python/mypy#6063
            records=cls._load_epw_records(epw_iter),
        )

    def to_epw(self, epw_file: AnyStrPath) -> None:
        with open(epw_file, "wt") as fp:
            fp.write(
                "\n".join(
                    (
                        self.location._to_epw_line(),  # type: ignore[attr-defined] # python/mypy#6063
                        self.design_conditions._to_epw_line(),  # type: ignore[attr-defined] # python/mypy#6063
                        self.typical_extreme_periods._to_epw_line(),  # type: ignore[attr-defined] # python/mypy#6063
                        self.ground_temperatures._to_epw_line(),  # type: ignore[attr-defined] # python/mypy#6063
                        self.holidays_daylight_saving._to_epw_line(),  # type: ignore[attr-defined] # python/mypy#6063
                        self.comments_1._to_epw_line(),  # type: ignore[attr-defined] # python/mypy#6063
                        self.comments_2._to_epw_line(),  # type: ignore[attr-defined] # python/mypy#6063
                        self.data_periods._to_epw_line(),  # type: ignore[attr-defined] # python/mypy#6063
                        *self._dump_epw_records(),
                    )
                )
                + "\n"
            )

    @classmethod
    def _load_epw_records(cls, epw_records: Iterator[str]) -> AnyRecords:
        return cls._load_epw_records_generic(
            (
                iter(
                    (data := tuple(epw_record.split(",")))
                    + ("",) * (len(cls.fields) - len(data))  # for bad epw
                )
                for epw_record in epw_records
            )
        )

    def _dump_epw_records(self) -> Iterator[str]:
        return self._dump_epw_records_generic()
