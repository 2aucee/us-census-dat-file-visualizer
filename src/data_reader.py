"""Read delimited or documented fixed-width Census text files."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence

import pandas as pd


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
    text: str,
    *,
    delimiter: str | None = None,
    has_header: bool = True,
) -> pd.DataFrame:
    """Read delimited records, with optional delimiter detection."""
    if not text.strip():
        raise ValueError("The uploaded file is empty.")
    separator = delimiter
    if separator is None:
        sample_lines = [line for line in text.splitlines() if line.strip()][:20]
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
            io.StringIO(text),
            sep=separator,
            engine="python",
            header=0 if has_header else None,
        )
    except (pd.errors.ParserError, UnicodeError) as error:
        raise ValueError(f"Could not parse the delimited file: {error}") from error


def read_fixed_width(
    text: str,
    *,
    names: Sequence[str],
    colspecs: Sequence[tuple[int, int]],
) -> pd.DataFrame:
    """Read fixed-width records using zero-based, end-exclusive pandas colspecs."""
    if not text.strip():
        raise ValueError("The uploaded file is empty.")
    if not names or len(names) != len(colspecs):
        raise ValueError("Each fixed-width field must have exactly one name and position range.")
    try:
        return pd.read_fwf(
            io.StringIO(text),
            colspecs=list(colspecs),
            names=list(names),
            header=None,
        )
    except (pd.errors.ParserError, ValueError) as error:
        raise ValueError(f"Could not parse the fixed-width file: {error}") from error
