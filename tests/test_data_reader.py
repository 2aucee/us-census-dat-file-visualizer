import io

import pytest
import pandas as pd

from src.data_reader import (
    decode_text,
    load_sep23pub_layout,
    parse_fixed_width_layout,
    read_delimited,
    read_fixed_width,
    read_sep23pub_csv,
    read_sep23pub_file,
)
from src.census_labels import (
    label_responses,
    prepare_chart_series,
    variable_label,
)


def test_read_delimited_with_header():
    frame = read_delimited("age,group\n30,A\n40,B\n", delimiter=",")
    assert frame.to_dict("list") == {"age": [30, 40], "group": ["A", "B"]}


def test_read_delimited_detects_separator():
    frame = read_delimited("age|group\n30|A\n40|B\n")
    assert frame.to_dict("list") == {"age": [30, 40], "group": ["A", "B"]}


def test_read_delimited_without_header():
    frame = read_delimited("30,A\n40,B\n", delimiter=",", has_header=False)
    assert frame.shape == (2, 2)
    assert frame.iloc[0].tolist() == [30, "A"]


def test_read_delimited_stream_selects_columns_and_limits_preview():
    stream = io.StringIO(
        "age,region,weight\n20,West,100\n30,East,200\n40,South,300\n"
    )
    preview = read_delimited(
        stream, delimiter=",", columns=["age", "weight"], nrows=2
    )
    assert preview.to_dict("list") == {"age": [20, 30], "weight": [100, 200]}


def test_read_delimited_pages_through_rows_after_the_header():
    page = read_delimited(
        "age,group\n20,A\n30,B\n40,C\n50,D\n",
        nrows=2,
        row_offset=2,
    )
    assert page.to_dict("list") == {"age": [40, 50], "group": ["C", "D"]}


def test_read_delimited_detects_separator_when_rows_exceed_sample_buffer():
    headers = [f"field_{index}" for index in range(422)]
    row = ["x" * 24 for _ in headers]
    text = ",".join(headers) + "\n" + ",".join(row) + "\n"
    frame = read_delimited(text, nrows=1)
    assert frame.shape == (1, 422)


def test_read_sep23pub_csv_selected_columns_and_row_limit():
    text = "HRHHID,PRSUPVOL,PWNRWGT\n00012,1,125.5\n00013,2,80.0\n"
    frame = read_sep23pub_csv(
        text, columns=["HRHHID", "PRSUPVOL"], nrows=1
    )
    assert frame.to_dict("list") == {"HRHHID": ["00012"], "PRSUPVOL": [1]}


def test_read_sep23pub_csv_keeps_identifier_codes_as_text():
    frame = read_sep23pub_csv("GESTFIPS,PRTAGE\n06,35\n")
    assert frame.loc[0, "GESTFIPS"] == "06"
    assert frame.loc[0, "PRTAGE"] == 35


def test_census_variables_and_documented_categories_are_readable():
    assert variable_label("PES16D") == "How often did you volunteer?"
    assert label_responses("PRSUPVOL", pd.Series([-1, 1, 2])).tolist() == [
        "N/A",
        "Volunteer",
        "Not a volunteer",
    ]
    assert label_responses("PEEDUCA", pd.Series([39, 43])).tolist() == [
        "High school diploma or equivalent",
        "Bachelor's degree",
    ]
    assert str(label_responses("PRSUPVOL", pd.Series([-1, 1, 2])).dtype) == "string"


def test_cps_demographic_and_supplement_codes_have_readable_labels():
    assert label_responses("GEREG", pd.Series([1, 4])).tolist() == [
        "Northeast",
        "West",
    ]
    assert label_responses("PESEX", pd.Series([1, 2])).tolist() == [
        "Male",
        "Female",
    ]
    assert label_responses("PRMARSTA", pd.Series([1, 7])).tolist() == [
        "Married, civilian spouse present",
        "Never married",
    ]
    assert label_responses("PES11", pd.Series([-1, -2, -3, -9, 3])).tolist() == [
        "N/A",
        "Don't know",
        "Refused",
        "No answer",
        "Not eligible to vote",
    ]


def test_official_cps_metadata_labels_additional_fields_and_codes():
    assert variable_label("UNKNOWN", year="2023") == (
        "Unlabeled Census field"
    )
    assert variable_label("HETENURE", year="2023") == (
        "Housing tenure"
    )
    assert label_responses(
        "HETENURE", pd.Series([1, 3, -1, 9]), year="2023"
    ).tolist() == [
        "Owned or being bought by a hh member",
        "Occupied without payment of cash rent",
        "N/A",
        "Code not listed in Census documentation",
    ]
    assert label_responses(
        "GESTFIPS", pd.Series(["06", "11"]), year="2023"
    ).tolist() == ["California", "District of Columbia"]
    assert label_responses(
        "HETENURE", pd.Series([1]), year="2023", include_code=True
    ).tolist() == ["Owned or being bought by a hh member (1)"]
    assert variable_label("HETENURE", year="2023", include_code=True) == (
        "Housing tenure (HETENURE)"
    )
    assert prepare_chart_series(
        "PRTAGE", pd.Series([25, 80]), year="2023"
    ).tolist() == [25, 80]


def test_common_cps_special_codes_are_labeled_for_other_fields():
    assert label_responses(
        "PES99", pd.Series([-9, -3, -2, -1, 1])
    ).tolist() == [
        "No answer",
        "Refused",
        "Don't know",
        "N/A",
        "1",
    ]


def test_not_in_universe_is_n_a_for_documented_and_undocumented_fields():
    assert label_responses("PES11", pd.Series([-1, 1])).tolist() == [
        "N/A",
        "Yes",
    ]
    assert label_responses(
        "PES16D", pd.Series([-1, 5]), documented=False
    ).tolist() == ["N/A", "5"]


def test_chart_series_keeps_numeric_measurements_numeric():
    series = prepare_chart_series("PRTAGE", pd.Series([-1, 25]))
    assert pd.isna(series.iloc[0])
    assert series.iloc[1] == 25
    assert pd.api.types.is_numeric_dtype(series)


def test_chart_series_labels_documented_categorical_fields():
    assert prepare_chart_series(
        "PRSUPVOL", pd.Series([-1, 1, 2])
    ).tolist() == [
        "N/A",
        "Volunteer",
        "Not a volunteer",
    ]


def test_parse_fixed_width_layout_and_read():
    names, colspecs = parse_fixed_width_layout("name,start,end\nAGE,1,2\nSEX,3,3\n")
    frame = read_fixed_width("251\n402\n", names=names, colspecs=colspecs)
    assert names == ["AGE", "SEX"]
    assert colspecs == [(0, 2), (2, 3)]
    assert frame.iloc[0].tolist() == [25, 1]


def test_sep23pub_layout_reads_documented_fields():
    names, colspecs = load_sep23pub_layout()
    assert len(names) == 424
    assert names[:6] == ["HRHHID", "HRMONTH", "HRYEAR4", "HURESPLI", "HUFINAL", "FILLER"]
    assert colspecs[names.index("HRMONTH")] == (15, 17)
    assert colspecs[names.index("PES1")] == (1000, 1002)
    assert colspecs[names.index("PWSRWGT")] == (1071, 1081)

    record = [" "] * 1081
    record[:15] = "000000000000001"
    record[15:17] = "09"
    record[1000:1002] = "01"
    frame = read_sep23pub_file("".join(record))
    assert frame.loc[0, "HRHHID"] == "000000000000001"
    assert frame.loc[0, "HRMONTH"] == 9
    assert frame.loc[0, "PES1"] == 1


@pytest.mark.parametrize(
    "layout",
    [
        "AGE,1,2\n",
        "name,start,end\nAGE,0,2\n",
        "name,start,end\nAGE,1,3\nAGE,4,5\n",
        "name,start,end\nAGE,1,3\nSEX,3,4\n",
    ],
)
def test_rejects_invalid_fixed_width_layout(layout):
    with pytest.raises(ValueError):
        parse_fixed_width_layout(layout)


def test_decode_windows_text():
    assert decode_text("café".encode("cp1252")) == "café"
