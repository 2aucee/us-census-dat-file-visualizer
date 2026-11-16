"""Human-readable labels for common September 2023 CPS fields and responses."""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd


VARIABLE_LABELS = {
    "HRMONTH": "Interview month",
    "HRYEAR4": "Interview year",
    "GEREG": "Census region",
    "GESTFIPS": "State FIPS code",
    "PERRP": "Relationship to household reference person",
    "PRTAGE": "Age",
    "PESEX": "Sex",
    "PEEDUCA": "Highest education level",
    "PRMARSTA": "Marital status",
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
    "PTS16E": "Volunteer hours in the past year (top-coded at 500)",
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


def variable_label(name: str) -> str:
    """Return a descriptive field name while keeping its Census code visible."""
    description = VARIABLE_LABELS.get(name) or FALLBACK_LABELS.get(name)
    if description is None:
        return name.replace("_", " ").title()
    return f"{description} ({name})"


def label_responses(name: str, values: pd.Series) -> pd.Series:
    """Replace documented numeric category codes with their response labels."""
    labels: Mapping[int, str] | None = RESPONSE_LABELS.get(name)
    if labels is None:
        return values

    def label(value: object) -> object:
        if pd.isna(value):
            return "Missing"
        try:
            code = int(value)
        except (TypeError, ValueError):
            return value
        if code in labels:
            return labels[code]
        if code < 0:
            return f"Other nonresponse ({code})"
        return f"Other response ({code})"

    return values.map(label)
