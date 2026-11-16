import pytest

from src.data_reader import (
    decode_text,
    parse_fixed_width_layout,
    read_delimited,
    read_fixed_width,
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


def test_parse_fixed_width_layout_and_read():
    names, colspecs = parse_fixed_width_layout("name,start,end\nAGE,1,2\nSEX,3,3\n")
    frame = read_fixed_width("251\n402\n", names=names, colspecs=colspecs)
    assert names == ["AGE", "SEX"]
    assert colspecs == [(0, 2), (2, 3)]
    assert frame.iloc[0].tolist() == [25, 1]


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
