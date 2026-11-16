from __future__ import annotations

import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from src.data_reader import (
    decode_text,
    load_sep23pub_layout,
    parse_fixed_width_layout,
    read_delimited,
    read_fixed_width,
    read_sep23pub_file,
)

st.set_page_config(page_title="Census Data Explorer", page_icon="📊", layout="wide")
sns.set_theme(style="whitegrid")

st.title("Census Data Explorer")
st.markdown(
    "Explore a Census text file in this app. Uploads are processed in memory and are "
    "not saved by the app. A hosted copy sends the file to its hosting provider; run "
    "the app locally if you do not want to upload data to a hosting service."
)

uploaded_file = st.file_uploader(
    "Choose a Census .dat, .txt, or delimited file",
    type=["dat", "txt", "csv", "tsv"],
)

if uploaded_file is None:
    st.info(
        "Upload a file to begin. The SEP23PUB layout is included; other fixed-width files need their official record layout."
    )
    st.stop()

try:
    is_sep23pub = Path(uploaded_file.name).name.casefold() == "sep23pub.dat"
    format_choice = st.radio(
        "How is the file organized?",
        ["Delimited / whitespace", "Fixed-width records"],
        index=1 if uploaded_file.name.casefold().endswith(".dat") else 0,
        horizontal=True,
    )

    if format_choice == "Delimited / whitespace":
        text = decode_text(uploaded_file.getvalue())
        delimiter_choice = st.selectbox(
            "Field separator",
            ["Detect automatically", "Comma", "Tab", "Pipe", "Whitespace"],
        )
        delimiter = {
            "Detect automatically": None,
            "Comma": ",",
            "Tab": "\t",
            "Pipe": "|",
            "Whitespace": r"\s+",
        }[delimiter_choice]
        has_header = st.checkbox("First row contains column names", value=True)
        data = read_delimited(text, delimiter=delimiter, has_header=has_header)
        use_sep23_layout = False
    else:
        if is_sep23pub:
            st.info("Using the official Census layout for sep23pub.dat.")
            field_names, field_colspecs = load_sep23pub_layout()
            uploaded_file.seek(0)
            file_text = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
            try:
                preview = read_sep23pub_file(file_text, nrows=100)
            finally:
                file_text.detach()
            use_sep23_layout = True
        else:
            st.caption(
                "Use the Census documentation for this exact file and supplement. "
                "Positions below are one-based and inclusive."
            )
            layout_text = st.text_area(
                "Paste the record layout as CSV",
                value="name,start,end\n",
                height=110,
                help="Include a header row and one row per field. Example: AGE,1,2",
            )
            field_names, field_colspecs = parse_fixed_width_layout(layout_text)
            use_sep23_layout = False
        uploaded_file.seek(0)
        if not use_sep23_layout:
            with io.TextIOWrapper(uploaded_file, encoding="utf-8-sig") as file_text:
                data = read_fixed_width(file_text, names=field_names, colspecs=field_colspecs)
except (UnicodeDecodeError, ValueError, pd.errors.ParserError) as error:
    st.error(str(error))
    st.stop()

if use_sep23_layout:
    if preview.empty or len(preview.columns) == 0:
        st.warning("No records or fields were found in the uploaded file.")
        st.stop()

    st.subheader("Data preview")
    st.dataframe(preview, use_container_width=True)
    st.caption("Preview is limited to the first 100 records.")
    st.subheader("Explore a variable")
    variable = st.selectbox("Variable to visualize", field_names)
    available_weights = [
        weight for weight in ("PWNRWGT", "PWSRWGT") if weight != variable
    ]
    weight_column = st.selectbox(
        "Optional weight field",
        ["Unweighted", *available_weights],
        help="These are the Census supplement weights. Weighted summaries here do not calculate CPS survey-design standard errors.",
    )
    columns_to_read = [variable]
    if weight_column != "Unweighted" and weight_column != variable:
        columns_to_read.append(weight_column)
    uploaded_file.seek(0)
    file_text = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
    try:
        data = read_sep23pub_file(file_text, columns=columns_to_read)
    except (UnicodeDecodeError, ValueError, pd.errors.ParserError) as error:
        st.error(str(error))
        st.stop()
    finally:
        file_text.detach()
    if data.empty:
        st.warning("No records were found in the uploaded file.")
        st.stop()

    metric_columns = st.columns(3)
    metric_columns[0].metric("Records", f"{len(data):,}")
    metric_columns[1].metric("Fields", f"{len(field_names):,}")
    metric_columns[2].metric(
        "Missing cells in preview",
        f"{int(preview.isna().sum().sum()):,}",
    )
    detail_data = preview
else:
    if data.empty or len(data.columns) == 0:
        st.warning("No records or columns were found. Check the file format and record layout.")
        st.stop()

    st.subheader("Data overview")
    metric_columns = st.columns(3)
    metric_columns[0].metric("Records", f"{len(data):,}")
    metric_columns[1].metric("Fields", f"{len(data.columns):,}")
    metric_columns[2].metric("Missing cells", f"{int(data.isna().sum().sum()):,}")
    st.dataframe(data.head(100), use_container_width=True)
    st.caption("Preview is limited to the first 100 rows.")

    st.subheader("Explore a variable")
    numeric_columns = data.select_dtypes(include="number").columns.tolist()
    all_columns = data.columns.tolist()
    variable = st.selectbox("Variable to visualize", all_columns)
    weight_options = ["Unweighted"] + numeric_columns
    weight_column = st.selectbox(
        "Optional weight field",
        weight_options,
        help="Weighted summaries are descriptive only; this does not account for CPS replicate weights or survey design.",
    )
    detail_data = data

series = data[variable]
is_numeric = pd.api.types.is_numeric_dtype(series)
if is_numeric:
    chart_type = st.radio("Chart", ["Distribution", "Summary statistics"], horizontal=True)
    values = pd.to_numeric(series, errors="coerce")
    if weight_column != "Unweighted" and chart_type == "Distribution":
        chart_data = pd.DataFrame(
            {"value": values, "weight": pd.to_numeric(data[weight_column], errors="coerce")}
        ).dropna()
        chart_data = chart_data[chart_data["weight"] > 0]
    else:
        chart_data = pd.DataFrame({"value": values}).dropna()

    if chart_data.empty:
        st.warning("No valid values are available for this selection.")
    elif chart_type == "Distribution":
        figure, axis = plt.subplots(figsize=(9, 4))
        if "weight" in chart_data:
            sns.histplot(data=chart_data, x="value", weights="weight", bins="auto", ax=axis)
            axis.set_ylabel("Weighted count")
        else:
            sns.histplot(data=chart_data, x="value", bins="auto", ax=axis)
            axis.set_ylabel("Count")
        axis.set_xlabel(str(variable))
        st.pyplot(figure)
        plt.close(figure)
    else:
        summary = chart_data["value"].describe().to_frame("value")
        if weight_column != "Unweighted":
            valid = pd.DataFrame(
                {"value": values, "weight": pd.to_numeric(data[weight_column], errors="coerce")}
            ).dropna()
            valid = valid[valid["weight"] > 0]
            if not valid.empty:
                summary.loc["weighted mean", "value"] = (
                    (valid["value"] * valid["weight"]).sum() / valid["weight"].sum()
                )
        st.dataframe(summary, use_container_width=True)
else:
    chart_data = pd.DataFrame({"value": series.astype("string")})
    if weight_column != "Unweighted":
        chart_data["weight"] = pd.to_numeric(data[weight_column], errors="coerce")
        chart_data = chart_data.dropna(subset=["value", "weight"])
        chart_data = chart_data[chart_data["weight"] > 0]
        counts = chart_data.groupby("value", observed=True)["weight"].sum()
        count_label = "Weighted count"
    else:
        counts = chart_data["value"].value_counts(dropna=True)
        count_label = "Count"
    counts = counts.nlargest(25).sort_values()
    if counts.empty:
        st.warning("No valid values are available for this selection.")
    else:
        figure, axis = plt.subplots(figsize=(9, max(4, min(9, len(counts) * 0.32))))
        counts.plot.barh(ax=axis)
        axis.set_xlabel(count_label)
        axis.set_ylabel(str(variable))
        st.pyplot(figure)
        plt.close(figure)
        st.caption("Showing up to 25 most frequent categories.")

with st.expander("Field details"):
    details = pd.DataFrame(
        {
            "dtype": detail_data.dtypes.astype(str),
            "missing": detail_data.isna().sum(),
            "distinct": detail_data.nunique(dropna=True),
        }
    )
    st.dataframe(details, use_container_width=True)
    if use_sep23_layout:
        st.caption("Field details are calculated from the 100-row preview.")
