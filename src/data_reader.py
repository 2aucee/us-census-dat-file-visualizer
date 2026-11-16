"""Read delimited or documented fixed-width Census text files."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TextIO

import pandas as pd


def load_sep23pub_layout() -> tuple[list[str], list[tuple[int, int]]]:
    """Load Census-documented positions for the September 2023 public CPS file."""
    layout_path = Path(__file__).parent / "layouts" / "sep23pub_layout.json"
    try:
        with layout_path.open(encoding="utf-8") as layout_file:
            layout = json.load(layout_file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not load the bundled SEP23PUB record layout: {error}") from error

    fields = layout.get("fields") if isinstance(layout, dict) else None
    if not isinstance(fields, list) or not fields:
        raise ValueError("The bundled SEP23PUB record layout is empty or invalid.")

    names: list[str] = []
    colspecs: list[tuple[int, int]] = []
    for field in fields:
        try:
            name = field["name"]
            start = int(field["start"])
            end = int(field["end"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("The bundled SEP23PUB record layout contains invalid fields.") from error
        if not isinstance(name, str) or not name or start < 1 or end < start:
            raise ValueError("The bundled SEP23PUB record layout contains invalid fields.")
        if name in names:
            raise ValueError(f"The bundled SEP23PUB layout has a duplicate field: {name}")
        names.append(name)
        colspecs.append((start - 1, end))

    ordered = sorted(colspecs)
    if any(current[0] < previous[1] for previous, current in zip(ordered, ordered[1:])):
        raise ValueError("The bundled SEP23PUB record layout contains overlapping fields.")
    return names, colspecs


def read_sep23pub_file(
    text: str | TextIO,
    *,
    columns: Sequence[str] | None = None,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Read the September 2023 CPS public file, preserving ID and geography codes."""
    names, colspecs = load_sep23pub_layout()
    text_fields = {
        name: str
        for name in (
            "HRHHID",
            "HRHHID2",
            "GESTFIPS",
            "GTCBSA",
            "GTCO",
            "GTCBSAST",
            "GTMETSTA",
            "GTINDVPC",
            "GTCBSASZ",
            "GTCSA",
        )
    }
    if columns is not None:
        text_fields = {name: kind for name, kind in text_fields.items() if name in columns}
    return read_fixed_width(
        text,
        names=names,
        colspecs=colspecs,
        dtype=text_fields,
        columns=columns,
        nrows=nrows,
    )


def read_sep23pub_csv(
    text: str | TextIO,
    *,
    columns: Sequence[str] | None = None,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Read selected columns from the Census-delimited September 2023 CPS file."""
    try:
        frame = pd.read_csv(
            io.StringIO(text) if isinstance(text, str) else text,
            usecols=list(columns) if columns is not None else None,
            nrows=nrows,
            dtype={
                name: str
                for name in (
                    "HRHHID",
                    "HRHHID2",
                    "GESTFIPS",
                    "GTCBSA",
                    "GTCO",
                    "GTCBSAST",
                    "GTMETSTA",
                    "GTINDVPC",
                    "GTCBSASZ",
                    "GTCSA",
                )
                if columns is None or name in columns
            },
        )
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
        raise ValueError(f"Could not parse the SEP23PUB CSV file: {error}") from error
    if frame.empty or len(frame.columns) == 0:
        raise ValueError("The SEP23PUB CSV file has no records or selected columns.")
    if columns is not None:
        frame = frame.loc[:, list(columns)]
    return frame


def decode_text(contents: bytes) -> str:
    """Decode common Census text encodings, raising if neither is valid."""
    try:
        return contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        return contents.decode("cp1252")


def parse_fixed_width_layout(layout_text: str) -> tuple[list[str], list[tuple[int, int]]]:
    """Parse CSV layout rows named name,start,end (one-based, inclusive positions)."""
    reader = csv.DictReader(io.StringIO(layout_text.strip()))
    expected = {"name", "start", "end"}
    if reader.fieldnames is None or not expected.issubset(
        {field.strip().lower() for field in reader.fieldnames}
    ):
        raise ValueError("Layout must have a header with name,start,end columns.")

    normalized_fields = {field.strip().lower(): field for field in reader.fieldnames}
    names: list[str] = []
    colspecs: list[tuple[int, int]] = []
    for line_number, row in enumerate(reader, start=2):
        try:
            name = (row[normalized_fields["name"]] or "").strip()
            start = int(row[normalized_fields["start"]])
            end = int(row[normalized_fields["end"]])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Invalid layout values on line {line_number}.") from error
        if not name or start < 1 or end < start:
            raise ValueError(
                f"Line {line_number}: provide a name and valid one-based start/end positions."
            )
        if name in names:
            raise ValueError(f"Duplicate field name: {name}")
        names.append(name)
        colspecs.append((start - 1, end))

    if not names:
        raise ValueError("The fixed-width layout has no field rows.")

    ordered = sorted(colspecs)
    if any(current[0] < previous[1] for previous, current in zip(ordered, ordered[1:])):
        raise ValueError("Fixed-width fields overlap; check the record layout.")
    return names, colspecs


def read_delimited(
    text: str | TextIO,
    *,
    delimiter: str | None = None,
    has_header: bool = True,
    columns: Sequence[str] | None = None,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Read delimited records, optionally selecting columns and limiting rows."""
    stream = io.StringIO(text) if isinstance(text, str) else text
    position = stream.tell()
    sample_lines = []
    for _ in range(20):
        line = stream.readline()
        if not line:
            break
        if line.strip():
            sample_lines.append(line.rstrip("\r\n"))
    stream.seek(position)
    if not sample_lines:
        raise ValueError("The uploaded file is empty.")
    separator = delimiter
    if separator is None:
        for candidate in (",", "\t", "|", ";"):
            parsed_rows = list(csv.reader(sample_lines, delimiter=candidate))
            field_counts = [len(row) for row in parsed_rows]
            if field_counts and len(set(field_counts)) == 1 and field_counts[0] > 1:
                separator = candidate
                break
        if separator is None:
            separator = r"\s+"
    try:
        return pd.read_csv(
            stream,
            sep=separator,
            engine="python" if separator == r"\s+" else "c",
            header=0 if has_header else None,
            usecols=list(columns) if columns is not None else None,
            nrows=nrows,
        )
    except (pd.errors.ParserError, UnicodeError) as error:
        raise ValueError(f"Could not parse the delimited file: {error}") from error


def read_fixed_width(
    text: str | TextIO,
    *,
    names: Sequence[str],
    colspecs: Sequence[tuple[int, int]],
    dtype: Mapping[str, type] | None = None,
    columns: Sequence[str] | None = None,
    nrows: int | None = None,
) -> pd.DataFrame:
    """Read fixed-width records using zero-based, end-exclusive pandas colspecs."""
    if isinstance(text, str):
        is_empty = not text.strip()
    else:
        position = text.tell()
        is_empty = not text.read(1)
        text.seek(position)
    if is_empty:
        raise ValueError("The uploaded file is empty.")
    if not names or len(names) != len(colspecs):
        raise ValueError("Each fixed-width field must have exactly one name and position range.")
    if len(set(names)) != len(names):
        raise ValueError("Fixed-width field names must be unique.")
    selected_names = list(names if columns is None else columns)
    if not selected_names or any(name not in names for name in selected_names):
        raise ValueError("Select one or more fields that exist in the fixed-width layout.")
    colspec_by_name = dict(zip(names, colspecs))
    ordered_fields = sorted(
        ((name, colspec_by_name[name]) for name in selected_names),
        key=lambda field: field[1][0],
    )
    try:
        frame = pd.read_fwf(
            io.StringIO(text) if isinstance(text, str) else text,
            colspecs=[colspec for _, colspec in ordered_fields],
            names=[name for name, _ in ordered_fields],
            header=None,
            dtype=dtype,
            nrows=nrows,
        )
        return frame.loc[:, selected_names]
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as error:
        raise ValueError(f"Could not parse the fixed-width file: {error}") from error
