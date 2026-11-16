"""Analysis helpers for the FBLA Community Engagement and Volunteering project."""

from __future__ import annotations

import gzip
import io
import zipfile
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from src.census_labels import label_responses
from src.data_reader import read_delimited

ANALYSIS_FIELDS = (
    "GEREG",
    "PRTAGE",
    "PESEX",
    "PEEDUCA",
    "PRMARSTA",
    "PES1",
    "PES7",
    "PES11",
    "PES12",
    "PES15",
    "PES16",
    "PES16A",
    "PES17",
    "PES18",
    "PRSUPVOL",
    "PWNRWGT",
)

INDICATORS: Mapping[str, tuple[str, str]] = {
    "Overall volunteering": ("PRSUPVOL", "Volunteer status"),
    "Formal volunteering": ("PES16", "Volunteered for an organization"),
    "Informal volunteering": ("PES16A", "Informal or occasional activities"),
    "Charitable giving over $25": ("PES18", "Non-political organization"),
    "Political giving over $25": ("PES17", "Political organization"),
    "Community improvement": ("PES7", "Joined neighbors for community improvement"),
    "Local election voting": ("PES11", "Voted in local elections"),
    "Public meeting attendance": ("PES12", "Attended a local public meeting"),
    "Organization membership": ("PES15", "Belonged to a group or organization"),
}

SEP17_COLSPECS: Mapping[str, tuple[int, int]] = {
    "GEREG": (88, 90),
    "PRTAGE": (121, 123),
    "PESEX": (128, 130),
    "PEEDUCA": (136, 138),
    "PRMARSTA": (158, 160),
    "PES1": (1000, 1002),
    "PES7": (1012, 1014),
    "PES11": (1020, 1022),
    "PES12": (1022, 1024),
    "PES15": (1028, 1030),
    "PES16": (1034, 1036),
    "PES16A": (1036, 1038),
    "PES17": (1087, 1089),
    "PES18": (1089, 1091),
    "PRSUPVOL": (1093, 1095),
    "PWNRWGT": (1097, 1107),
}

YEAR_DATA_URLS = {
    2017: "https://www2.census.gov/programs-surveys/cps/datasets/2017/supp/sep17pub.zip",
    2019: "https://www2.census.gov/programs-surveys/cps/datasets/2019/supp/sep19pub.csv",
    2021: "https://www2.census.gov/programs-surveys/cps/datasets/2021/supp/sep21pub.csv",
    2023: "https://www2.census.gov/programs-surveys/cps/datasets/2023/supp/sep23pub.csv",
}

YEAR_DOCUMENTATION_URLS = {
    2017: "https://www2.census.gov/programs-surveys/cps/techdocs/cpssep17.pdf",
    2019: "https://www2.census.gov/programs-surveys/cps/techdocs/cpssept19.pdf",
    2021: "https://www2.census.gov/programs-surveys/cps/techdocs/cpssept21.pdf",
    2023: "https://www2.census.gov/programs-surveys/cps/techdocs/cpssep23.pdf",
}
MAX_SEP17_UNCOMPRESSED_BYTES = 250 * 1024 * 1024


def year_from_filename(filename: str) -> int | None:
    """Return a supported survey year for an official public-use file name."""
    basename = Path(filename).name.casefold()
    for year in YEAR_DATA_URLS:
        short_year = str(year)[-2:]
        if basename in {
            f"sep{short_year}pub.csv",
            f"sep{short_year}pub.dat",
            f"sep{short_year}pub.dat.gz",
            f"sep{short_year}pub.zip",
        }:
            return year
    return None


def _read_sep17_fwf(uploaded_file: object) -> pd.DataFrame:
    """Read selected fields from the official 2017 fixed-width file or archive."""
    filename = str(getattr(uploaded_file, "name", "")).casefold()
    field_names = sorted(SEP17_COLSPECS, key=lambda name: SEP17_COLSPECS[name][0])
    colspecs = [SEP17_COLSPECS[name] for name in field_names]

    def parse(binary_stream: object) -> pd.DataFrame:
        text_stream = io.TextIOWrapper(binary_stream, encoding="utf-8-sig")
        try:
            return pd.read_fwf(
                text_stream,
                colspecs=colspecs,
                names=field_names,
                header=None,
                dtype={"PWNRWGT": "string"},
            )
        finally:
            text_stream.detach()

    uploaded_file.seek(0)  # type: ignore[attr-defined]
    if filename.endswith(".zip"):
        with zipfile.ZipFile(uploaded_file) as archive:  # type: ignore[arg-type]
            members = [
                member
                for member in archive.infolist()
                if Path(member.filename).name.casefold() == "sep17pub.dat"
            ]
            if len(members) != 1:
                raise ValueError("The archive must contain exactly one sep17pub.dat file.")
            if members[0].file_size > MAX_SEP17_UNCOMPRESSED_BYTES:
                raise ValueError("The uncompressed 2017 data file exceeds the 250 MB limit.")
            with archive.open(members[0]) as member_stream:
                return parse(member_stream)
    if filename.endswith(".gz"):
        compressed_stream = gzip.GzipFile(fileobj=uploaded_file)  # type: ignore[arg-type]
        contents = compressed_stream.read(MAX_SEP17_UNCOMPRESSED_BYTES + 1)
        if len(contents) > MAX_SEP17_UNCOMPRESSED_BYTES:
            raise ValueError("The uncompressed 2017 data file exceeds the 250 MB limit.")
        return parse(io.BytesIO(contents))
    if filename.endswith(".dat"):
        return parse(uploaded_file)
    raise ValueError("2017 data must be sep17pub.dat, sep17pub.dat.gz, or sep17pub.zip.")


def read_cps_wave(uploaded_file: object, year: int) -> pd.DataFrame:
    """Read analysis fields for one supported Census CEV release."""
    if year == 2017:
        return _read_sep17_fwf(uploaded_file)
    if year not in YEAR_DATA_URLS:
        raise ValueError(f"Unsupported survey year: {year}.")

    uploaded_file.seek(0)  # type: ignore[attr-defined]
    header = pd.read_csv(uploaded_file, nrows=0, encoding="utf-8-sig")
    selected_fields = [name for name in ANALYSIS_FIELDS if name in header.columns]
    if "PWNRWGT" not in selected_fields:
        raise ValueError(f"The {year} file is missing the PWNRWGT survey weight.")
    if not any(name in selected_fields for name in ("PRSUPVOL", "PES16")):
        raise ValueError(f"The {year} file is missing a volunteering response field.")
    uploaded_file.seek(0)  # type: ignore[attr-defined]
    text_stream = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
    try:
        return read_delimited(text_stream, columns=selected_fields)
    finally:
        text_stream.detach()


def weighted_indicator_trends(
    waves: Mapping[int, pd.DataFrame],
) -> pd.DataFrame:
    """Calculate weighted yes rates among valid responses for each survey wave."""
    rows: list[dict[str, object]] = []
    for year in sorted(waves):
        frame = waves[year]
        if "PWNRWGT" not in frame:
            continue
        weight = pd.to_numeric(frame["PWNRWGT"], errors="coerce")
        for key, (variable, definition) in INDICATORS.items():
            if variable not in frame:
                continue
            response = pd.to_numeric(frame[variable], errors="coerce")
            valid = response.isin([1, 2]) & weight.notna() & (weight > 0)
            valid_weights = weight[valid]
            denominator = float(valid_weights.sum())
            if denominator <= 0:
                continue
            yes_weight = float(valid_weights[response[valid].eq(1)].sum())
            rows.append(
                {
                    "year": year,
                    "indicator": key,
                    "variable": variable,
                    "description": definition,
                    "valid_responses": int(valid.sum()),
                    "weighted_valid_population": denominator,
                    "yes_weighted_population": yes_weight,
                    "yes_percent": yes_weight / denominator * 100,
                }
            )
    return pd.DataFrame(rows)


def _age_group(age: pd.Series) -> pd.Series:
    numeric_age = pd.to_numeric(age, errors="coerce").mask(lambda values: values < 16)
    return pd.cut(
        numeric_age,
        bins=[16, 25, 45, 65, 121],
        labels=["16-24", "25-44", "45-64", "65+"],
        right=False,
    )


def build_analysis_export(waves: Mapping[int, pd.DataFrame]) -> pd.DataFrame:
    """Build a harmonized, labeled respondent-level file without Census IDs."""
    output: list[pd.DataFrame] = []
    code_labels = {
        "GEREG": "region",
        "PESEX": "sex",
        "PEEDUCA": "education",
        "PRMARSTA": "marital_status",
    }
    response_labels = {
        "PRSUPVOL": "overall_volunteering",
        "PES16": "formal_volunteering",
        "PES16A": "informal_volunteering",
        "PES17": "political_giving_over_25",
        "PES18": "charitable_giving_over_25",
        "PES7": "community_improvement",
        "PES11": "local_election_voting",
        "PES12": "public_meeting_attendance",
        "PES15": "organization_membership",
    }
    for year, frame in sorted(waves.items()):
        clean = pd.DataFrame(index=frame.index)
        clean.insert(0, "survey_year", year)
        if "PRTAGE" in frame:
            clean["age"] = pd.to_numeric(frame["PRTAGE"], errors="coerce").mask(
                lambda values: values < 16
            )
            clean["age_group"] = _age_group(frame["PRTAGE"])
        for variable, output_name in code_labels.items():
            if variable in frame:
                clean[output_name] = label_responses(variable, frame[variable])
        for variable, output_name in response_labels.items():
            if variable in frame:
                clean[output_name] = label_responses(variable, frame[variable])
        if "PWNRWGT" in frame:
            weight = pd.to_numeric(frame["PWNRWGT"], errors="coerce")
            clean["survey_weight"] = weight.where(weight > 0)
        output.append(clean.reset_index(drop=True))
    if not output:
        return pd.DataFrame()
    return pd.concat(output, ignore_index=True)


def weighted_age_group_rates(
    frame: pd.DataFrame, year: int
) -> pd.DataFrame:
    """Calculate overall volunteering rates by age group for one wave."""
    required = {"PRTAGE", "PRSUPVOL", "PWNRWGT"}
    if not required.issubset(frame.columns):
        return pd.DataFrame(columns=["age_group", "yes_percent", "valid_responses"])
    data = pd.DataFrame(
        {
            "age_group": _age_group(frame["PRTAGE"]),
            "response": pd.to_numeric(frame["PRSUPVOL"], errors="coerce"),
            "weight": pd.to_numeric(frame["PWNRWGT"], errors="coerce"),
        }
    )
    data = data[data["response"].isin([1, 2]) & (data["weight"] > 0)]
    grouped = data.groupby("age_group", observed=True)
    rows = []
    for age_group, group in grouped:
        rows.append(
            {
                "age_group": age_group,
                "yes_percent": (
                    group.loc[group["response"].eq(1), "weight"].sum()
                    / group["weight"].sum()
                    * 100
                ),
                "valid_responses": len(group),
                "year": year,
            }
        )
    return pd.DataFrame(rows)


def trend_recommendation(trends: pd.DataFrame) -> str:
    """Create a cautious, evidence-linked pilot recommendation from observed rates."""
    if trends.empty:
        return "Upload at least one supported CEV survey file to calculate weighted estimates."
    years = sorted(trends["year"].unique())
    if len(years) < 2:
        return (
            "One survey wave is available. It can establish a weighted baseline, but "
            "upload another year before describing a trend or recommending a response "
            "to a change over time."
        )
    first_year, last_year = years[0], years[-1]
    comparisons = trends[trends["year"].isin([first_year, last_year])].pivot(
        index="indicator", columns="year", values="yes_percent"
    )
    if first_year not in comparisons or last_year not in comparisons:
        return "The selected years do not share enough measures for a reliable trend comparison."
    comparisons = comparisons.dropna(subset=[first_year, last_year])
    if comparisons.empty:
        return "No common indicators have valid weighted responses in both selected years."
    changes = comparisons[last_year] - comparisons[first_year]
    declining = changes[changes < 0]
    if not declining.empty:
        indicator = str(declining.idxmin())
        change = float(changes[indicator])
        evidence = (
            f"its weighted valid-response rate declined by {abs(change):.1f} "
            f"percentage points between {first_year} and {last_year}"
        )
    else:
        indicator = str(comparisons[last_year].idxmin())
        current_rate = float(comparisons.loc[indicator, last_year])
        evidence = (
            f"it had the lowest observed weighted valid-response rate "
            f"({current_rate:.1f}%) in {last_year}"
        )
    return (
        f"Consider a low-barrier community partnership focused on {indicator.lower()}: "
        f"{evidence}. A feasible pilot could provide a named community coordinator, "
        "partner organizations, flexible short-shift or remote options, and a modest "
        "outreach budget. Recheck participation after one year; these descriptive "
        "survey patterns do not establish why a rate changed."
    )


def export_csv(frame: pd.DataFrame) -> bytes:
    """Serialize a UTF-8-with-BOM CSV suitable for spreadsheet software."""
    return frame.to_csv(index=False).encode("utf-8-sig")


def census_source(year: int, documentation: bool = False) -> str:
    """Return the official source URL for a supported year."""
    sources = YEAR_DOCUMENTATION_URLS if documentation else YEAR_DATA_URLS
    if year not in sources:
        raise ValueError(f"Unsupported survey year: {year}.")
    return sources[year]
