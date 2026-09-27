import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------------------------
# PAGE SETUP
# -------------------------------------------------

st.set_page_config(
    page_title="Lebanon Consumer Price Crisis",
    page_icon="📊",
    layout="wide"
)

st.title("Lebanon's Consumer Price Crisis")
st.write(
    "Explore how food and general consumer prices changed in Lebanon "
    "and drill down into food inflation within individual years."
)


# -------------------------------------------------
# LOAD AND CLEAN THE DATA
# -------------------------------------------------

df = pd.read_csv("dataset.csv")

# Convert important columns to numbers.
# The first row of the dataset contains metadata rather than observations,
# so invalid values become NaN and are removed.
df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

df = df.dropna(subset=["Year", "Value", "Item"])

df["Year"] = df["Year"].astype(int)


# -------------------------------------------------
# SPLIT THE DATA INTO VARIABLES
# -------------------------------------------------

index_data = df[
    df["Item"].isin(
        [
            "Consumer Prices, Food Indices (2015 = 100)",
            "Consumer Prices, General Indices (2015 = 100)"
        ]
    )
].copy()

inflation_data = df[
    df["Item"] == "Food price inflation"
].copy()


# -------------------------------------------------
# INTERACTIONS
# -------------------------------------------------

st.subheader("Explore the data")

year_min = max(
    int(index_data["Year"].min()),
    int(inflation_data["Year"].min())
)

year_max = min(
    int(index_data["Year"].max()),
    int(inflation_data["Year"].max())
)

selected_range = st.slider(
    "Choose a period for the overall CPI trend:",
    min_value=year_min,
    max_value=year_max,
    value=(year_min, year_max)
)

start_year, end_year = selected_range

# The dropdown options still depend on the selected slider range,
# but we will display the dropdown later on the page.
available_years = sorted(
    inflation_data[
        (inflation_data["Year"] >= start_year) &
        (inflation_data["Year"] <= end_year)
    ]["Year"].unique()
)


# -------------------------------------------------
# VISUALIZATION 1
# CPI INDICES OVER TIME
# -------------------------------------------------

st.header("1. Overall Consumer Price Trends")

filtered_indices = index_data[
    (index_data["Year"] >= start_year) &
    (index_data["Year"] <= end_year)
].copy()

annual_indices = (
    filtered_indices
    .groupby(["Year", "Item"], as_index=False)["Value"]
    .mean()
)

annual_indices["Item"] = annual_indices["Item"].replace(
    {
        "Consumer Prices, Food Indices (2015 = 100)": "Food Price Index",
        "Consumer Prices, General Indices (2015 = 100)": "General Price Index"
    }
)

fig1 = px.line(
    annual_indices,
    x="Year",
    y="Value",
    color="Item",
    markers=True,
    labels={
        "Value": "Index Value (2015 = 100)",
        "Item": "Price Index"
    }
)

fig1.update_layout(
    xaxis_title="Year",
    yaxis_title="Index Value (2015 = 100)",
    legend_title=""
)

st.plotly_chart(fig1, use_container_width=True)

# Create an insight that changes with the selected year range.
index_summary = annual_indices.pivot(
    index="Year",
    columns="Item",
    values="Value"
)

first_year = int(index_summary.index.min())
last_year = int(index_summary.index.max())

food_start = index_summary.loc[first_year, "Food Price Index"]
food_end = index_summary.loc[last_year, "Food Price Index"]

general_start = index_summary.loc[first_year, "General Price Index"]
general_end = index_summary.loc[last_year, "General Price Index"]

if first_year == last_year:
    st.info(
        f"In {last_year}, the Food Price Index averaged {food_end:,.1f}, "
        f"compared with {general_end:,.1f} for the General Price Index."
    )
else:
    st.info(
        f"From {first_year} to {last_year}, the Food Price Index increased "
        f"from {food_start:,.1f} to {food_end:,.1f}, while the General Price "
        f"Index increased from {general_start:,.1f} to {general_end:,.1f}. "
        f"This allows the selected period to be compared directly rather than "
        f"using the full 2001–2023 history every time."
    )

st.markdown("---")

st.subheader("Drill down into one year")
st.write(
    "Choose one year from the selected period to examine monthly food inflation in more detail."
)

selected_year = st.selectbox(
    "Choose a year for the monthly inflation chart:",
    available_years,
    index=len(available_years) - 1
)

st.write("")

# -------------------------------------------------
# VISUALIZATION 2
# MONTHLY FOOD INFLATION
# -------------------------------------------------

st.header(f"2. Monthly Food Inflation in {selected_year}")

year_inflation = inflation_data[
    inflation_data["Year"] == selected_year
].copy()

month_order = [
    "January", "February", "March", "April",
    "May", "June", "July", "August",
    "September", "October", "November", "December"
]

year_inflation["Month"] = pd.Categorical(
    year_inflation["Month"],
    categories=month_order,
    ordered=True
)

year_inflation = year_inflation.sort_values("Month")

fig2 = px.bar(
    year_inflation,
    x="Month",
    y="Value",
    labels={
        "Value": "Food Inflation (%)",
        "Month": "Month"
    }
)

fig2.update_layout(
    xaxis_title="Month",
    yaxis_title="Food Inflation (%)"
)

st.plotly_chart(fig2, use_container_width=True)

if len(year_inflation) < 12:
    st.caption(
        f"Note: {selected_year} contains {len(year_inflation)} months of data "
        "in the source dataset, so only available months are shown."
    )

highest_row = year_inflation.loc[year_inflation["Value"].idxmax()]
lowest_row = year_inflation.loc[year_inflation["Value"].idxmin()]

highest_month = highest_row["Month"]
highest_value = highest_row["Value"]

lowest_month = lowest_row["Month"]
lowest_value = lowest_row["Value"]

st.info(
    f"In {selected_year}, food inflation was highest in "
    f"{highest_month} at {highest_value:.1f}% and lowest in "
    f"{lowest_month} at {lowest_value:.1f}%. "
    f"This monthly view shows how inflation changed within the year "
    f"instead of relying only on an annual average."
)

# -------------------------------------------------
# DESIGN JUSTIFICATIONS
# -------------------------------------------------

st.header("Interaction Design")

with st.expander("Why use a year-range slider?"):
    st.write(
        "The year-range slider helps the user answer the question: "
        "'What happened to consumer prices during the period I want to study?' "
        "A slider is the appropriate support for this visualization because years have a natural chronological order "
        "and the user is selecting a continuous period rather than unrelated categories. "
        "Restricting the chart to a selected period can also reduce visual clutter "
        "and focus attention on the years that matter to the user's question."
    )

with st.expander("Why use a year dropdown?"):
    st.write(
        "The year dropdown helps the user answer the question: "
        "'What did food inflation look like month by month during one specific year?' "
        "A dropdown is also suitable because only one year needs to be examined at a time. "
        "Its choices are also linked to the years within the range of the slider: only years inside the "
        "selected period are available. This creates an overview-to-detail interaction "
        "that allows the user to first choose a broader context and then narrow things down."
    )



st.caption("Data source: FAO / HumData – Lebanon Consumer Price Indices")