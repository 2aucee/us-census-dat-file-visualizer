import gzip
import io
import zipfile

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
from src.fbla_analysis import (
    build_analysis_export,
    read_cps_wave,
    trend_recommendation,
    weighted_age_group_rates,
    weighted_indicator_trends,
    year_from_filename,
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
    assert variable_label("PES16D") == "How often did you volunteer? (PES16D)"
    assert label_responses("PRSUPVOL", pd.Series([-1, 1, 2])).tolist() == [
        "N/A",
        "Volunteer (1)",
        "Not a volunteer (2)",
    ]
    assert label_responses("PEEDUCA", pd.Series([39, 43])).tolist() == [
        "High school diploma or equivalent (39)",
        "Bachelor's degree (43)",
    ]
    assert str(label_responses("PRSUPVOL", pd.Series([-1, 1, 2])).dtype) == "string"


def test_cps_demographic_and_supplement_codes_have_readable_labels():
    assert label_responses("GEREG", pd.Series([1, 4])).tolist() == [
        "Northeast (1)",
        "West (4)",
    ]
    assert label_responses("PESEX", pd.Series([1, 2])).tolist() == [
        "Male (1)",
        "Female (2)",
    ]
    assert label_responses("PRMARSTA", pd.Series([1, 7])).tolist() == [
        "Married, civilian spouse present (1)",
        "Never married (7)",
    ]
    assert label_responses("PES11", pd.Series([-1, -2, -3, -9, 3])).tolist() == [
        "N/A",
        "Don't know (-2)",
        "Refused (-3)",
        "No answer (-9)",
        "Not eligible to vote (3)",
    ]


def test_common_cps_special_codes_are_labeled_for_other_fields():
    assert label_responses(
        "PES99", pd.Series([-9, -3, -2, -1, 1])
    ).tolist() == [
        "No answer (-9)",
        "Refused (-3)",
        "Don't know (-2)",
        "N/A",
        "1",
    ]


def test_not_in_universe_is_n_a_for_documented_and_undocumented_fields():
    assert label_responses("PES11", pd.Series([-1, 1])).tolist() == [
        "N/A",
        "Yes (1)",
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
        "Volunteer (1)",
        "Not a volunteer (2)",
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


def test_fbla_year_recognition():
    assert year_from_filename("sep17pub.zip") == 2017
    assert year_from_filename("sep19pub.csv") == 2019
    assert year_from_filename("sep21pub.csv") == 2021
    assert year_from_filename("sep23pub.csv") == 2023
    assert year_from_filename("another.csv") is None


def test_fbla_csv_reader_loads_only_relevant_columns():
    upload = io.BytesIO(
        b"PRSUPVOL,PWNRWGT,unused\n1,10,ignored\n2,20,ignored\n"
    )
    upload.name = "sep23pub.csv"
    frame = read_cps_wave(upload, 2023)
    assert frame.columns.tolist() == ["PRSUPVOL", "PWNRWGT"]
    assert frame["PRSUPVOL"].tolist() == [1, 2]


def test_fbla_2017_zip_reader_uses_official_fixed_width_positions():
    record = bytearray(b" " * 1107)
    values = {
        "GEREG": (88, "04"),
        "PRTAGE": (121, "35"),
        "PESEX": (128, "02"),
        "PEEDUCA": (136, "43"),
        "PRMARSTA": (158, "07"),
        "PES7": (1012, "01"),
        "PES11": (1020, "02"),
        "PES12": (1022, "01"),
        "PES15": (1028, "01"),
        "PES16": (1034, "01"),
        "PES16A": (1036, "02"),
        "PES17": (1087, "02"),
        "PES18": (1089, "01"),
        "PRSUPVOL": (1093, "01"),
        "PWNRWGT": (1097, "0000000100"),
    }
    for start, value in values.values():
        record[start : start + len(value)] = value.encode("ascii")
    archive_contents = io.BytesIO()
    with zipfile.ZipFile(archive_contents, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("sep17pub.dat", bytes(record) + b"\n")
    upload = io.BytesIO(archive_contents.getvalue())
    upload.name = "sep17pub.zip"

    frame = read_cps_wave(upload, 2017)

    assert frame.loc[0, "GEREG"] == 4
    assert frame.loc[0, "PRTAGE"] == 35
    assert frame.loc[0, "PRSUPVOL"] == 1
    assert float(frame.loc[0, "PWNRWGT"]) == 100


def test_fbla_2017_gzip_reader():
    record = bytearray(b" " * 1107)
    record[1093:1095] = b"01"
    record[1097:1107] = b"0000000100"
    upload = io.BytesIO(gzip.compress(bytes(record) + b"\n"))
    upload.name = "sep17pub.dat.gz"

    frame = read_cps_wave(upload, 2017)

    assert frame.loc[0, "PRSUPVOL"] == 1
    assert float(frame.loc[0, "PWNRWGT"]) == 100


def test_fbla_weighted_rates_exclude_invalid_and_zero_weight_records():
    frame = pd.DataFrame(
        {
            "PRSUPVOL": [1, 2, -1, 1],
            "PES11": [1, 3, 2, 1],
            "PWNRWGT": [2, 3, 100, 0],
        }
    )

    trends = weighted_indicator_trends({2023: frame}).set_index("indicator")

    assert trends.loc["Overall volunteering", "valid_responses"] == 2
    assert trends.loc["Overall volunteering", "weighted_valid_population"] == 5
    assert trends.loc["Overall volunteering", "yes_percent"] == 40
    assert trends.loc["Local election voting", "valid_responses"] == 2
    assert trends.loc["Local election voting", "yes_percent"] == pytest.approx(200 / 102)


def test_fbla_analysis_export_is_labeled_and_age_rates_are_weighted():
    frame = pd.DataFrame(
        {
            "PRTAGE": [20, 30, 70],
            "GEREG": [1, 2, 4],
            "PESEX": [1, 2, 2],
            "PEEDUCA": [39, 43, 46],
            "PRMARSTA": [7, 1, 4],
            "PRSUPVOL": [1, 2, 1],
            "PES16": [1, 2, -1],
            "PWNRWGT": [2, 3, 5],
        }
    )

    export = build_analysis_export({2023: frame})
    age_rates = weighted_age_group_rates(frame, 2023).set_index("age_group")

    assert export.loc[0, "region"] == "Northeast (1)"
    assert export.loc[0, "overall_volunteering"] == "Volunteer (1)"
    assert export.loc[0, "age_group"] == "16-24"
    assert age_rates.loc["16-24", "yes_percent"] == 100
    assert age_rates.loc["25-44", "yes_percent"] == 0
    assert "HRHHID" not in export.columns


def test_fbla_recommendation_does_not_claim_a_trend_from_one_wave():
    trends = pd.DataFrame(
        [{"year": 2023, "indicator": "Overall volunteering", "yes_percent": 45}]
    )

    assert "upload another year" in trend_recommendation(trends)


def test_fbla_recommendation_uses_the_largest_observed_decline():
    trends = pd.DataFrame(
        [
            {"year": 2017, "indicator": "Overall volunteering", "yes_percent": 55},
            {"year": 2023, "indicator": "Overall volunteering", "yes_percent": 40},
            {"year": 2017, "indicator": "Formal volunteering", "yes_percent": 25},
            {"year": 2023, "indicator": "Formal volunteering", "yes_percent": 23},
        ]
    )

    recommendation = trend_recommendation(trends)

    assert "overall volunteering" in recommendation
    assert "declined by 15.0 percentage points" in recommendation
