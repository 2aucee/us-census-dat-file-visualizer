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
from src.census_labels import label_responses, variable_label


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
    assert variable_label("PES16D") == "How often did you volunteer? (PES16D)"
    assert label_responses("PRSUPVOL", pd.Series([-1, 1, 2])).tolist() == [
        "Not in universe",
        "Volunteer",
        "Not a volunteer",
    ]
    assert label_responses("PEEDUCA", pd.Series([39, 43])).tolist() == [
        "High school diploma or equivalent",
        "Bachelor's degree",
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
