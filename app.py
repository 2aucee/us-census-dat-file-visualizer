from __future__ import annotations

import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from src.data_reader import (
    load_sep23pub_layout,
    parse_fixed_width_layout,
    read_delimited,
    read_fixed_width,
    read_sep23pub_csv,
    read_sep23pub_file,
)
from src.census_labels import (
    VARIABLE_LABELS,
    label_responses,
    prepare_chart_series,
    variable_label,
)

st.set_page_config(page_title="Census Data Explorer", page_icon="📊", layout="wide")
sns.set_theme(style="whitegrid", context="notebook", palette="crest")

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

preview_rows = st.selectbox(
    "Rows to show in the preview",
    [100, 500, 1_000],
    index=1,
    format_func=lambda rows: f"{rows:,} rows",
    help="The preview is capped at 1,000 rows to keep wide files responsive.",
)

if uploaded_file is None:
    st.info(
        "Upload a file to begin. The SEP23PUB layout is included; other fixed-width files need their official record layout."
    )
    st.stop()

try:
    is_sep23pub = Path(uploaded_file.name).name.casefold() == "sep23pub.dat"
    is_sep23pub_csv = Path(uploaded_file.name).name.casefold() == "sep23pub.csv"
    is_sep19pub_csv = Path(uploaded_file.name).name.casefold() == "sep19pub.csv"
    is_sep21pub_csv = Path(uploaded_file.name).name.casefold() == "sep21pub.csv"
    is_recognized_cps_csv = (
        is_sep19pub_csv or is_sep21pub_csv or is_sep23pub_csv
    )
    is_streamed_delimited = False
    if is_sep23pub or is_sep23pub_csv:
        field_names, _ = load_sep23pub_layout()
        preview_fields = [
            name
            for name in (
                "PRTAGE",
                "PESEX",
                "PEEDUCA",
                "GEREG",
                "PRSUPVOL",
                "PES16D",
                "PTS16E",
                "PES11",
                "PES12",
                "PES15",
                "PES17",
                "PES18",
                "PWNRWGT",
            )
            if name in field_names
        ]
        if is_sep23pub_csv:
            st.info(
                "Recognized the September 2023 CPS CSV. The app reads a short preview "
                "first, then only the selected variable and optional weight."
            )
            uploaded_file.seek(0)
            preview = read_sep23pub_csv(
                uploaded_file, columns=preview_fields, nrows=preview_rows
            )
        else:
            st.info("Using the official Census layout for sep23pub.dat.")
            uploaded_file.seek(0)
            file_text = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
            try:
                preview = read_sep23pub_file(
                    file_text, columns=preview_fields, nrows=preview_rows
                )
            finally:
                file_text.detach()
        use_sep23_layout = True
    else:
        format_choice = st.radio(
            "How is the file organized?",
            ["Delimited / whitespace", "Fixed-width records"],
            index=1 if uploaded_file.name.casefold().endswith(".dat") else 0,
            horizontal=True,
        )

        if format_choice == "Delimited / whitespace":
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
            uploaded_file.seek(0)
            file_text = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
            try:
                preview = read_delimited(
                    file_text,
                    delimiter=delimiter,
                    has_header=has_header,
                    nrows=preview_rows,
                )
            finally:
                file_text.detach()
            field_names = list(preview.columns)
            data = preview
            is_streamed_delimited = True
            use_sep23_layout = False
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
    readable_preview = preview.rename(columns=variable_label)
    for column in preview.columns:
        readable_preview[variable_label(column)] = label_responses(
            column, preview[column]
        )
    st.dataframe(readable_preview, width="stretch")
    st.caption(f"Preview shows up to {preview_rows:,} records.")
    st.caption(
        "CPS special values are spelled out where they occur (for example, "
        "Not in universe (-1), Don't know (-2), Refused (-3), and No answer (-9)). "
        "The original code stays in parentheses."
    )
    st.subheader("Explore a variable")
    show_all_fields = st.checkbox(
        "Show all fields, including Census codes without built-in descriptions"
    )
    labeled_fields = [
        name for name in field_names if name in VARIABLE_LABELS
    ]
    variable_options = field_names if show_all_fields else labeled_fields
    if not variable_options:
        variable_options = field_names
        st.info("No built-in labels are available for this file's fields.")
    default_variable = (
        variable_options.index("PRSUPVOL")
        if "PRSUPVOL" in variable_options
        else 0
    )
    variable = st.selectbox(
        "Variable to visualize",
        variable_options,
        index=default_variable,
        format_func=variable_label,
    )
    available_weights = [
        weight for weight in ("PWNRWGT", "PWSRWGT") if weight != variable
    ]
    weight_column = st.selectbox(
        "Optional weight field",
        ["Unweighted", *available_weights],
        format_func=lambda name: (
            "Unweighted"
            if name == "Unweighted"
            else variable_label(name)
        ),
        help="These are the Census supplement weights. Weighted summaries here do not calculate CPS survey-design standard errors.",
    )
    columns_to_read = [variable]
    if weight_column != "Unweighted" and weight_column != variable:
        columns_to_read.append(weight_column)
    try:
        uploaded_file.seek(0)
        if is_sep23pub_csv:
            data = read_sep23pub_csv(uploaded_file, columns=columns_to_read)
        else:
            file_text = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
            try:
                data = read_sep23pub_file(file_text, columns=columns_to_read)
            finally:
                file_text.detach()
    except (UnicodeDecodeError, ValueError, pd.errors.ParserError) as error:
        st.error(str(error))
        st.stop()
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
    if is_streamed_delimited:
        if is_recognized_cps_csv:
            release = "2019" if is_sep19pub_csv else "2021" if is_sep21pub_csv else "2023"
            st.info(
                f"Recognized the September {release} CPS CSV. The app reads only "
                "the selected variable and optional weight across the full file."
            )
            readable_preview = preview.rename(columns=variable_label)
            for column in preview.columns:
                readable_preview[variable_label(str(column))] = label_responses(
                    str(column),
                    preview[column],
                    documented=not is_sep21pub_csv,
                )
            st.dataframe(readable_preview, width="stretch")
            st.caption(
                "Not-in-universe (-1) values are shown as N/A. Response labels "
                "are shown when available; other values retain their original code."
            )
        else:
            st.dataframe(preview, width="stretch")
        st.caption(f"Preview shows up to {preview_rows:,} rows.")

        st.subheader("Explore a variable")
        numeric_columns = preview.select_dtypes(include="number").columns.tolist()
        default_variable = (
            field_names.index("PRSUPVOL")
            if is_recognized_cps_csv and "PRSUPVOL" in field_names
            else 0
        )
        variable = st.selectbox(
            "Variable to visualize",
            field_names,
            index=default_variable,
            format_func=lambda name: (
                variable_label(str(name))
                if is_recognized_cps_csv
                else str(name)
            ),
        )
        weight_options = ["Unweighted"] + numeric_columns
        weight_column = st.selectbox(
            "Optional weight field",
            weight_options,
            format_func=lambda name: (
                "Unweighted"
                if name == "Unweighted"
                else variable_label(str(name))
                if is_recognized_cps_csv
                else str(name)
            ),
            help="Weighted summaries are descriptive only; this does not account for CPS replicate weights or survey design.",
        )
        columns_to_read = [variable]
        if weight_column != "Unweighted" and weight_column != variable:
            columns_to_read.append(weight_column)
        uploaded_file.seek(0)
        file_text = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
        try:
            data = read_delimited(
                file_text,
                delimiter=delimiter,
                has_header=has_header,
                columns=columns_to_read,
            )
        finally:
            file_text.detach()
        if data.empty:
            st.warning("No records were found for this selection.")
            st.stop()

        metric_columns = st.columns(3)
        metric_columns[0].metric("Records", f"{len(data):,}")
        metric_columns[1].metric("Fields", f"{len(preview.columns):,}")
        metric_columns[2].metric(
            "Missing cells in preview",
            f"{int(preview.isna().sum().sum()):,}",
        )
        detail_data = preview
    else:
        metric_columns = st.columns(3)
        metric_columns[0].metric("Records", f"{len(data):,}")
        metric_columns[1].metric("Fields", f"{len(data.columns):,}")
        metric_columns[2].metric("Missing cells", f"{int(data.isna().sum().sum()):,}")
        st.dataframe(data.head(preview_rows), width="stretch")
        st.caption(f"Preview shows up to {preview_rows:,} rows.")

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

if use_sep23_layout or is_recognized_cps_csv:
    documented = not is_sep21pub_csv
    series = prepare_chart_series(
        variable, data[variable], documented=documented
    )
else:
    series = data[variable]
plot_variable = (
    variable_label(variable)
    if use_sep23_layout or is_recognized_cps_csv
    else str(variable)
)
is_numeric = pd.api.types.is_numeric_dtype(series)
if is_numeric:
    numeric_view = st.radio(
        "Interpret numeric values as",
        ["Numbers", "Category codes"],
        horizontal=True,
        help="Choose Category codes for variables whose numbers represent labeled groups.",
    )
    is_numeric = numeric_view == "Numbers"

if is_numeric:
    chart_type = st.selectbox("Chart", ["Histogram", "Box plot", "Summary statistics"])
    values = pd.to_numeric(series, errors="coerce")
    if weight_column != "Unweighted" and chart_type == "Histogram":
        chart_data = pd.DataFrame(
            {"value": values, "weight": pd.to_numeric(data[weight_column], errors="coerce")}
        ).dropna()
        chart_data = chart_data[chart_data["weight"] > 0]
    else:
        chart_data = pd.DataFrame({"value": values}).dropna()

    if chart_data.empty:
        st.warning("No valid values are available for this selection.")
    elif chart_type == "Histogram":
        figure, axis = plt.subplots(figsize=(10, 5), dpi=120)
        if "weight" in chart_data:
            sns.histplot(
                data=chart_data,
                x="value",
                weights="weight",
                bins="auto",
                color="#2563EB",
                edgecolor="white",
                linewidth=0.6,
                ax=axis,
            )
            axis.set_ylabel("Weighted count")
        else:
            sns.histplot(
                data=chart_data,
                x="value",
                bins="auto",
                kde=values.nunique() > 10,
                color="#2563EB",
                edgecolor="white",
                linewidth=0.6,
                ax=axis,
            )
            axis.set_ylabel("Count")
        axis.set_xlabel(plot_variable)
        axis.set_title(f"Distribution of {plot_variable}", loc="left", weight="bold")
        axis.grid(axis="y", alpha=0.25)
        axis.grid(axis="x", visible=False)
        sns.despine(ax=axis)
        figure.tight_layout()
        st.pyplot(figure)
        plt.close(figure)
    elif chart_type == "Box plot":
        figure, axis = plt.subplots(figsize=(10, 3.5), dpi=120)
        sns.boxplot(
            x=chart_data["value"],
            color="#60A5FA",
            width=0.45,
            showmeans=True,
            meanprops={
                "marker": "D",
                "markerfacecolor": "#F97316",
                "markeredgecolor": "white",
                "markersize": 7,
            },
            ax=axis,
        )
        axis.set_xlabel(plot_variable)
        axis.set_title(f"Spread of {plot_variable}", loc="left", weight="bold")
        axis.grid(axis="x", alpha=0.25)
        axis.grid(axis="y", visible=False)
        sns.despine(ax=axis, left=True)
        figure.tight_layout()
        st.pyplot(figure)
        plt.close(figure)
        if weight_column != "Unweighted":
            st.caption("Box plots are unweighted; the selected weight is not applied.")
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
        summary.index.name = "Statistic"
        st.dataframe(summary, width="stretch")
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
    top_counts = counts.nlargest(10)
    if len(counts) > len(top_counts):
        top_counts.loc["Other categories"] = counts.drop(top_counts.index).sum()
    counts = top_counts.sort_values()
    if counts.empty:
        st.warning("No valid values are available for this selection.")
    else:
        chart_type = st.selectbox("Chart", ["Bar chart", "Donut chart"])
        if chart_type == "Bar chart":
            figure, axis = plt.subplots(
                figsize=(10, max(4, min(8, len(counts) * 0.42))),
                dpi=120,
            )
            colors = sns.color_palette("crest", n_colors=len(counts))
            bars = axis.barh(counts.index.astype(str), counts.values, color=colors)
            axis.bar_label(bars, fmt="%.0f", padding=4, fontsize=9)
            axis.set_xlabel(count_label)
            axis.set_ylabel("")
            axis.set_title(
                f"Most common responses for {plot_variable}",
                loc="left",
                weight="bold",
            )
            axis.grid(axis="x", alpha=0.25)
            axis.grid(axis="y", visible=False)
            axis.set_axisbelow(True)
            axis.margins(x=0.15)
            sns.despine(ax=axis, left=True)
            figure.tight_layout()
            st.pyplot(figure)
            plt.close(figure)
        else:
            donut_counts = counts.copy()
            figure, axis = plt.subplots(figsize=(8, 5), dpi=120)
            colors = sns.color_palette("crest", n_colors=len(donut_counts))
            wedges, _, _ = axis.pie(
                donut_counts.values,
                startangle=90,
                counterclock=False,
                colors=colors,
                wedgeprops={"width": 0.42, "edgecolor": "white", "linewidth": 2},
                autopct=lambda pct: f"{pct:.0f}%" if pct >= 4 else "",
                pctdistance=0.78,
                textprops={"color": "#1F2937", "fontsize": 9},
            )
            axis.text(
                0,
                0,
                f"{len(donut_counts)}\nresponses",
                ha="center",
                va="center",
                fontsize=12,
                weight="bold",
                color="#1F2937",
            )
            axis.legend(
                wedges,
                [str(category) for category in donut_counts.index],
                title=plot_variable,
                loc="center left",
                bbox_to_anchor=(1, 0.5),
                frameon=False,
            )
            axis.set_title("Response share", loc="left", weight="bold")
            figure.tight_layout()
            st.pyplot(figure)
            plt.close(figure)
        st.caption("Showing the top 10 categories; remaining values are grouped as Other.")

with st.expander("Field details"):
    details = pd.DataFrame(
        {
            "dtype": detail_data.dtypes.astype(str),
            "missing": detail_data.isna().sum(),
            "distinct": detail_data.nunique(dropna=True),
        }
    )
    st.dataframe(details, width="stretch")
    if use_sep23_layout or is_recognized_cps_csv:
        st.caption(
            f"Field details are calculated from the {preview_rows:,}-row preview."
        )
