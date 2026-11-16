"""Human-readable labels for common CPS fields and response categories."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import pandas as pd


VARIABLE_LABELS = {
    "HRMONTH": "Interview month",
    "HRYEAR4": "Interview year",
    "HURESPLI": "Respondent's household line number",
    "HUFINAL": "Interview result",
    "HULANGCODE": "Interview language",
    "HETENURE": "Housing tenure",
    "HEHOUSUT": "Type of home",
    "HETELHHD": "Telephone in the home",
    "HETELAVL": "Telephone available elsewhere",
    "HEPHONEO": "Phone interview allowed",
    "HEFAMINC": "Family income range",
    "HUTYPEA": "Type A non-interview reason",
    "HUTYPB": "Type B non-interview reason",
    "HUTYPC": "Type C non-interview reason",
    "HWHHWGT": "Household survey weight",
    "HRINTSTA": "Household interview result",
    "HRNUMHOU": "People in household",
    "HRHTYPE": "Household type",
    "HRMIS": "Survey rotation month",
    "HUINTTYP": "Interview method",
    "GEREG": "Census region",
    "GESTFIPS": "State",
    "PERRP": "Relationship to household reference person",
    "PRTAGE": "Age",
    "PESEX": "Sex",
    "PEEDUCA": "Highest education level",
    "PRMARSTA": "Marital status, including military spouse status",
    "PES1": "How often did you spend time with friends and family?",
    "PES2": "How often did you discuss issues with friends and family?",
    "PES4": "How often did you spend time with neighbors?",
    "PES5": "How often did you discuss issues with neighbors?",
    "PES6": "How often did neighbors help one another?",
    "PES7": "Joined neighbors to improve the community",
    "PES9": "How often did you post views about issues online?",
    "PES10": "How often did you follow news about issues?",
    "PES11": "Voted in local elections",
    "PES12": "Attended a public meeting about a local issue",
    "PES13": "Contacted a public official to express an opinion",
    "PES14": "Bought or boycotted products based on company values",
    "PES15": "Belonged to a group or organization",
    "PES15A": "Number of groups or organizations",
    "PES16": "Volunteered for an organization",
    "PES16A": "Did informal or occasional volunteer activities",
    "PES16D": "How often did you volunteer?",
    "PTS16E": "Volunteer hours in the past year",
    "PES16F": "How much volunteering was in person versus online?",
    "PES17": "Donated over $25 to a political organization",
    "PES18": "Donated over $25 to a non-political organization",
    "PRSUPINT": "Supplement interview status",
    "PRSUPVOL": "Volunteer status",
    "PRSELF": "Self-response status",
    "PWNRWGT": "Supplement nonresponse weight",
    "PWSRWGT": "Supplement self-response weight",
}

FALLBACK_LABELS = {
    "FILLER": "Unused field",
    "HRHHID": "Household identifier",
    "HRHHID2": "Household identifier (part 2)",
    "PESEX": "Sex",
    "PRTAGE": "Age",
    "PWNRWGT": "Supplement nonresponse weight",
    "PWSRWGT": "Supplement self-response weight",
}

RESPONSE_LABELS: dict[str, dict[int, str]] = {
    "HRMONTH": {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    },
    "GEREG": {1: "Northeast", 2: "Midwest", 3: "South", 4: "West"},
    "PESEX": {1: "Male", 2: "Female"},
    "PEEDUCA": {
        31: "Less than 1st grade",
        32: "1st-4th grade",
        33: "5th-6th grade",
        34: "7th-8th grade",
        35: "9th grade",
        36: "10th grade",
        37: "11th grade",
        38: "12th grade, no diploma",
        39: "High school diploma or equivalent",
        40: "Some college, no degree",
        41: "Associate degree, occupational",
        42: "Associate degree, academic",
        43: "Bachelor's degree",
        44: "Master's degree",
        45: "Professional degree",
        46: "Doctorate degree",
    },
    "PRMARSTA": {
        1: "Married, civilian spouse present",
        2: "Married, military spouse present",
        3: "Married, spouse absent",
        4: "Widowed",
        5: "Divorced",
        6: "Separated",
        7: "Never married",
    },
    "PRSUPINT": {-1: "Not in universe", 1: "Interview", 2: "Non-interview"},
    "PRSUPVOL": {-1: "Not in universe", 1: "Volunteer", 2: "Not a volunteer"},
    "PRSELF": {-1: "Not in universe", 1: "Self-response", 2: "Proxy response"},
    "PES1": {
        -3: "Refused",
        -2: "Don't know",
        -1: "Not in universe",
        1: "Basically every day",
        2: "A few times a week",
        3: "A few times a month",
        4: "Once a month",
        5: "Less than once a month",
        6: "Not at all",
    },
    "PES2": {
        -9: "No answer",
        -3: "Refused",
        -2: "Don't know",
        -1: "Not in universe",
        1: "Basically every day",
        2: "A few times a week",
        3: "A few times a month",
        4: "Once a month",
        5: "Less than once a month",
        6: "Not at all",
    },
    "PES4": {
        -9: "No answer",
        -3: "Refused",
        -2: "Don't know",
        -1: "Not in universe",
        1: "Basically every day",
        2: "A few times a week",
        3: "A few times a month",
        4: "Once a month",
        5: "Less than once a month",
        6: "Not at all",
    },
    "PES5": {
        -9: "No answer",
        -3: "Refused",
        -2: "Don't know",
        -1: "Not in universe",
        1: "Basically every day",
        2: "A few times a week",
        3: "A few times a month",
        4: "Once a month",
        5: "Less than once a month",
        6: "Not at all",
    },
    "PES6": {
        -9: "No answer",
        -3: "Refused",
        -2: "Don't know",
        -1: "Not in universe",
        1: "Basically every day",
        2: "A few times a week",
        3: "A few times a month",
        4: "Once a month",
        5: "Less than once a month",
        6: "Not at all",
    },
    "PES7": {
        -9: "No answer",
        -3: "Refused",
        -2: "Don't know",
        1: "Yes",
        2: "No",
    },
    "PES9": {
        -9: "No answer",
        -3: "Refused",
        -2: "Don't know",
        -1: "Not in universe",
        1: "Basically every day",
        2: "A few times a week",
        3: "A few times a month",
        4: "Once a month",
        5: "Less than once a month",
        6: "Not at all",
    },
    "PES10": {
        -9: "No answer",
        -3: "Refused",
        -2: "Don't know",
        -1: "Not in universe",
        1: "Basically every day",
        2: "A few times a week",
        3: "A few times a month",
        4: "Once a month",
        5: "Less than once a month",
        6: "Not at all",
    },
}

for question in ("PES11", "PES12", "PES13", "PES14", "PES15", "PES16", "PES16A", "PES17", "PES18"):
    RESPONSE_LABELS[question] = {
        -9: "No answer",
        -3: "Refused",
        -2: "Don't know",
        -1: "Not in universe",
        1: "Yes",
        2: "No",
    }

RESPONSE_LABELS["PES11"][3] = "Not eligible to vote"
RESPONSE_LABELS["PES15A"] = {
    -9: "No answer",
    -3: "Refused",
    -2: "Don't know",
    -1: "Not in universe",
    1: "One",
    2: "Two",
    3: "Three",
    4: "Four",
    5: "Five",
    6: "Six",
    7: "Seven or more",
}
RESPONSE_LABELS["PES16D"] = {
    -9: "No answer",
    -3: "Refused",
    -2: "Don't know",
    -1: "Not in universe",
    1: "Basically every day",
    2: "A few times a week",
    3: "A few times a month",
    4: "Once a month",
    5: "Less than once a month",
    6: "Not at all",
}
RESPONSE_LABELS["PES16F"] = {
    -9: "No answer",
    -3: "Refused",
    -2: "Don't know",
    -1: "Not in universe",
    1: "All in person",
    2: "More in person than online",
    3: "Evenly split",
    4: "More online than in person",
    5: "All online",
}
RESPONSE_LABELS["GESTFIPS"] = {
    1: "Alabama",
    2: "Alaska",
    4: "Arizona",
    5: "Arkansas",
    6: "California",
    8: "Colorado",
    9: "Connecticut",
    10: "Delaware",
    11: "District of Columbia",
    12: "Florida",
    13: "Georgia",
    15: "Hawaii",
    16: "Idaho",
    17: "Illinois",
    18: "Indiana",
    19: "Iowa",
    20: "Kansas",
    21: "Kentucky",
    22: "Louisiana",
    23: "Maine",
    24: "Maryland",
    25: "Massachusetts",
    26: "Michigan",
    27: "Minnesota",
    28: "Mississippi",
    29: "Missouri",
    30: "Montana",
    31: "Nebraska",
    32: "Nevada",
    33: "New Hampshire",
    34: "New Jersey",
    35: "New Mexico",
    36: "New York",
    37: "North Carolina",
    38: "North Dakota",
    39: "Ohio",
    40: "Oklahoma",
    41: "Oregon",
    42: "Pennsylvania",
    44: "Rhode Island",
    45: "South Carolina",
    46: "South Dakota",
    47: "Tennessee",
    48: "Texas",
    49: "Utah",
    50: "Vermont",
    51: "Virginia",
    53: "Washington",
    54: "West Virginia",
    55: "Wisconsin",
    56: "Wyoming",
}

SPECIAL_RESPONSE_LABELS = {
    -9: "No answer",
    -3: "Refused",
    -2: "Don't know",
    -1: "Not in universe",
}


def _load_cps_metadata() -> dict[str, dict[str, dict[str, object]]]:
    path = Path(__file__).parent / "layouts" / "cps_public_labels.json"
    try:
        with path.open(encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Could not load bundled Census labels: {error}") from error
    releases = metadata.get("releases") if isinstance(metadata, dict) else None
    if not isinstance(releases, dict):
        raise RuntimeError("The bundled Census labels have an invalid format.")
    return releases


CPS_METADATA = _load_cps_metadata()


def _field_metadata(name: str, year: str | None = None) -> dict[str, object]:
    years = [year, *[item for item in ("2023", "2021", "2019") if item != year]]
    merged: dict[str, object] = {}
    for release in reversed([item for item in years if item]):
        fields = CPS_METADATA.get(release, {})
        field = fields.get(name, {})
        if isinstance(field, dict):
            merged.update(field)
    return merged


def _response_labels(name: str, year: str | None = None) -> dict[int, str]:
    if year is None:
        metadata = _field_metadata(name)
    else:
        metadata = CPS_METADATA.get(year, {}).get(name, {})
    raw_labels = metadata.get("responses", {})
    labels = {
        int(code): str(label)
        for code, label in raw_labels.items()
    } if isinstance(raw_labels, dict) else {}
    labels.update(RESPONSE_LABELS.get(name, {}))
    return labels


def variable_label(
    name: str, *, year: str | None = None, include_code: bool = False
) -> str:
    """Return a readable field name, optionally including its Census code."""
    description = VARIABLE_LABELS.get(name) or FALLBACK_LABELS.get(name)
    if description is None:
        metadata_label = _field_metadata(name, year).get("label")
        if isinstance(metadata_label, str) and metadata_label:
            description = metadata_label
    if description is None:
        description = "Unlabeled Census field"
    return f"{description} ({name})" if include_code else description


def unique_variable_labels(
    names: list[str], *, year: str | None = None, include_code: bool = False
) -> dict[str, str]:
    """Make display labels unique without showing codes unless needed."""
    labels = {
        name: variable_label(name, year=year, include_code=include_code)
        for name in names
    }
    counts: dict[str, int] = {}
    for label in labels.values():
        key = label.casefold()
        counts[key] = counts.get(key, 0) + 1
    return {
        name: f"{label} — {name}" if counts[label.casefold()] > 1 else label
        for name, label in labels.items()
    }


def label_responses(
    name: str,
    values: pd.Series,
    *,
    documented: bool = True,
    year: str | None = None,
    include_code: bool = False,
) -> pd.Series:
    """Translate documented categories and common CPS special codes."""
    labels: Mapping[int, str] | None = (
        _response_labels(name, year) if documented else None
    )

    def label(value: object) -> object:
        if pd.isna(value):
            return "Missing"
        try:
            code = int(value)
            if float(value) != code:
                return value
        except (TypeError, ValueError):
            return value
        if code == -1:
            return "N/A"
        if labels is not None and code in labels:
            return f"{labels[code]} ({code})" if include_code else labels[code]
        if code in SPECIAL_RESPONSE_LABELS:
            return (
                f"{SPECIAL_RESPONSE_LABELS[code]} ({code})"
                if include_code
                else SPECIAL_RESPONSE_LABELS[code]
            )
        if labels:
            return (
                f"Code not listed in Census documentation ({code})"
                if include_code
                else "Code not listed in Census documentation"
            )
        return value

    return values.map(label).astype("string")


def prepare_chart_series(
    name: str,
    values: pd.Series,
    *,
    documented: bool = True,
    year: str | None = None,
) -> pd.Series:
    """Keep numeric fields numeric while translating documented categories."""
    if documented and _response_labels(name, year):
        return label_responses(name, values, year=year)
    if pd.api.types.is_numeric_dtype(values):
        return pd.to_numeric(values, errors="coerce").mask(
            values.isin(SPECIAL_RESPONSE_LABELS)
        )
    return label_responses(name, values, documented=documented)
