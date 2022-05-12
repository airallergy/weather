from os import PathLike

AnyPath = str | bytes | PathLike[str] | PathLike[bytes]
AnyFieldSchema = tuple[str | type]
AnyField = int | float | str
AnyRecords = tuple[tuple[AnyField]]
