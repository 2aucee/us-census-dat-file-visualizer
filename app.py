from __future__ import annotations

import io
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

from src.data_reader import read_delimited
from src.census_labels import (
    label_responses,
    prepare_chart_series,
    variable_label,
)

st.set_page_config(page_title="Census Data Explorer", page_icon="📊", layout="wide")
sns.set_theme(style="whitegrid", context="notebook", palette="crest")

st.title("Census Data Explorer")
st.markdown(
    "Upload a CSV file to view its table and explore columns. Uploads are processed "
    "in memory and aren't saved by the app. If you use the hosted site, the file "
    "is sent to its hosting provider."
)

uploaded_file = st.file_uploader(
    "Choose a CSV file",
    type=["csv"],
)

STUDENT_FRIENDLY_CPS_FIELDS = (
    "PRTAGE",
    "PESEX",
    "PEEDUCA",
    "PEMARITL",
    "PRMARSTA",
    "GEREG",
    "GESTFIPS",
    "HEFAMINC",
    "PRSUPVOL",
    "PES16",
    "PES16D",
    "PTS16E",
    "PES17",
    "PES18",
)

if uploaded_file is None:
    st.info("Upload a file to begin.")
    st.stop()

try:
    upload_name = Path(uploaded_file.name).name.casefold()
    release = next(
        (
            year
            for year in ("2019", "2021", "2023")
            if upload_name == f"sep{year[-2:]}pub.csv"
        ),
        None,
    )
    is_recognized_cps_csv = release is not None
    uploaded_file.seek(0)
    file_text = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
    try:
        header_preview = read_delimited(file_text, nrows=1)
    finally:
        file_text.detach()
    field_names = list(header_preview.columns)
    if is_recognized_cps_csv:
        field_names = [
            name for name in field_names if not str(name).upper().startswith("FILLER")
        ]
    if not field_names:
        st.warning("No columns were found. Check that the CSV has a header row.")
        st.stop()

    if is_recognized_cps_csv:
        st.info(
            f"Recognized the September {release} CPS CSV. Census labels are "
            "shown where the official documentation defines them."
        )
except (UnicodeDecodeError, ValueError, pd.errors.ParserError) as error:
    st.error(str(error))
    st.stop()

st.subheader("Explore a variable")
include_codes = False
show_all_cps_fields = False
if is_recognized_cps_csv:
    with st.expander("Census display options"):
        show_all_cps_fields = st.checkbox(
            "Show all Census columns, including IDs and survey-processing fields",
            help="The student view hides household IDs, weights, flags, and other technical fields. Turn this on to access every column.",
        )
        include_codes = st.checkbox(
            "Show Census codes next to names and responses",
            help="Codes are hidden by default. Numeric measurements such as age and hours remain numbers.",
        )

if is_recognized_cps_csv and not show_all_cps_fields:
    available_fields = [
        name for name in STUDENT_FRIENDLY_CPS_FIELDS if name in field_names
    ]
    if not available_fields:
        available_fields = field_names
else:
    available_fields = field_names

default_variable = (
    available_fields.index("PRSUPVOL")
    if is_recognized_cps_csv and "PRSUPVOL" in available_fields
    else 0
)
variable = st.selectbox(
    "Variable to visualize",
    available_fields,
    index=default_variable,
    format_func=lambda name: (
        variable_label(
            str(name), year=release, include_code=include_codes
        )
        if is_recognized_cps_csv
        else str(name)
    ),
    key="variable_to_visualize",
)
if is_recognized_cps_csv:
    st.caption(
        "Showing student-friendly demographic and volunteer fields. Enable all "
        "Census columns above to find the full codebook, IDs, weights, and survey details."
    )
    default_table_fields = available_fields
    table_columns = st.multiselect(
        "Columns in the table",
        options=available_fields,
        default=default_table_fields,
        format_func=lambda name: variable_label(
            str(name), year=release, include_code=include_codes
        ),
        key=(
            "all_census_table_columns"
            if show_all_cps_fields
            else "student_census_table_columns"
        ),
    )
else:
    table_columns = field_names

if not table_columns:
    st.info("Choose at least one column to show in the table.")
    st.stop()

available_weights = (
    [name for name in ("PWNRWGT", "PWSRWGT") if name in field_names and name != variable]
    if is_recognized_cps_csv
    else []
)
weight_column = st.selectbox(
    "Optional weight field",
    ["Unweighted", *available_weights],
    format_func=lambda name: (
        "Unweighted"
        if name == "Unweighted" or not is_recognized_cps_csv
        else variable_label(
            str(name), year=release, include_code=include_codes
        )
    ),
    help="Weighted summaries are descriptive only and do not account for CPS survey-design standard errors.",
)
columns_to_read = [variable]
if weight_column != "Unweighted":
    columns_to_read.append(weight_column)

try:
    uploaded_file.seek(0)
    file_text = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
    try:
        data = read_delimited(file_text, columns=columns_to_read)
    finally:
        file_text.detach()
except (UnicodeDecodeError, ValueError, pd.errors.ParserError) as error:
    st.error(str(error))
    st.stop()

if data.empty:
    st.warning("No data rows were found in the uploaded CSV.")
    st.stop()

records = len(data)
rows_per_page = st.selectbox(
    "Rows per table page",
    [50, 100, 250, 500],
    index=1,
    format_func=lambda rows: f"{rows:,} rows",
)
page_count = max(1, (records + rows_per_page - 1) // rows_per_page)
upload_signature = (uploaded_file.name, uploaded_file.size)
if st.session_state.get("_table_upload") != upload_signature:
    st.session_state["_table_upload"] = upload_signature
    st.session_state["table_page"] = 1
if st.session_state.get("table_page", 1) > page_count:
    st.session_state["table_page"] = page_count
page_number = st.number_input(
    "Table page",
    min_value=1,
    max_value=page_count,
    step=1,
    key="table_page",
)
row_offset = (page_number - 1) * rows_per_page
try:
    uploaded_file.seek(0)
    file_text = io.TextIOWrapper(uploaded_file, encoding="utf-8-sig")
    try:
        table_page = read_delimited(
            file_text,
            columns=table_columns,
            nrows=rows_per_page,
            row_offset=row_offset,
        )
    finally:
        file_text.detach()
except (UnicodeDecodeError, ValueError, pd.errors.ParserError) as error:
    st.error(str(error))
    st.stop()

metric_columns = st.columns(3)
metric_columns[0].metric("Records", f"{records:,}")
metric_columns[1].metric("Columns in file", f"{len(field_names):,}")
metric_columns[2].metric(
    "Blank values in selected column",
    f"{int(data[variable].isna().sum()):,}",
)
st.subheader("Data table")
if is_recognized_cps_csv:
    readable_table = table_page.copy()
    column_labels = {
        column: variable_label(
            str(column), year=release, include_code=include_codes
        )
        for column in table_page.columns
    }
    readable_table.columns = list(column_labels.values())
    for column in table_page.columns:
        readable_table[column_labels[column]] = label_responses(
            str(column),
            table_page[column],
            year=release,
            include_code=include_codes,
        )
    st.dataframe(
        readable_table,
        width="stretch",
        column_config={
            label: st.column_config.Column(
                label,
                help=f"Census variable: {name}",
                width="large",
            )
            for name, label in column_labels.items()
        },
    )
    st.caption(
        f"Page {page_number:,} of {page_count:,}; showing {len(table_columns):,} "
        f"of {len(field_names):,} columns. The chart and record count use all "
        f"{records:,} rows. {'Census codes are shown' if include_codes else 'Census codes are hidden'}; "
        "age and hours remain numeric."
    )
else:
    st.dataframe(table_page, width="stretch")
    st.caption(
        f"Page {page_number:,} of {page_count:,}. The chart and record count use "
        "all rows. Headers and values are kept as provided because this CSV has "
        "no bundled codebook."
    )

if is_recognized_cps_csv:
    series = prepare_chart_series(variable, data[variable], year=release)
else:
    series = data[variable]
plot_variable = (
    variable_label(variable, year=release, include_code=include_codes)
    if is_recognized_cps_csv
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
