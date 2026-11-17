from pathlib import Path
import sys
import pandas as pd
import streamlit as st
import plotly.express as px

TASK_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = TASK_DIR / "OUTPUT"
OUTPUT_DIR.mkdir(exist_ok=True)
DEFAULT_DATA = Path(r"D:\MY DATA\PROGRAMMING\Auspify\TASK1\OUTPUT\netflix_cleaned.csv")

class NetflixTrendAnalyzer:
    def __init__(self, csv_path):
        self.csv_path = Path(csv_path)
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Cleaned dataset not found: {self.csv_path}")
        self.df = pd.read_csv(self.csv_path)
        if "release_year" not in self.df.columns:
            raise ValueError("Required column 'release_year' is missing.")
        self.df["release_year"] = pd.to_numeric(self.df["release_year"], errors="coerce")
        self.df = self.df.dropna(subset=["release_year"]).copy()
        self.df["release_year"] = self.df["release_year"].astype(int)

    def yearly_releases(self):
        result = self.df.groupby("release_year").size().reset_index(name="content_count")
        result = result.sort_values("release_year")
        result["yearly_change"] = result["content_count"].diff()
        result["growth_rate_pct"] = result["content_count"].pct_change().mul(100)
        return result

    def save_outputs(self):
        yearly = self.yearly_releases()
        yearly.to_csv(OUTPUT_DIR / "yearly_releases.csv", index=False)
        fig = px.line(yearly, x="release_year", y="content_count", markers=True,
                      title="Netflix Titles by Release Year",
                      labels={"release_year":"Release year", "content_count":"Number of titles"})
        fig.write_html(OUTPUT_DIR / "release_year_trend.html")
        summary = [
            f"Total titles with a valid release year: {len(self.df):,}",
            f"Years covered: {yearly.release_year.min()}–{yearly.release_year.max()}",
            f"Peak release year: {int(yearly.loc[yearly.content_count.idxmax(), 'release_year'])}",
            f"Peak-year titles: {int(yearly.content_count.max()):,}",
            "Note: release year is the title's listed release year, not necessarily the year Netflix added it."
        ]
        (OUTPUT_DIR / "trend_summary.txt").write_text("\n".join(summary), encoding="utf-8")
        return yearly, summary

st.set_page_config(page_title="Task 4 | Netflix Trends", page_icon="📈", layout="wide")
st.title("Task 4 — Trend Analysis by Release Year")
st.caption("Explore annual title counts, growth and decline, and historical release patterns.")
with st.sidebar:
    st.header("Dataset")
    csv_path = st.text_input("Cleaned CSV path", str(DEFAULT_DATA))
    run_export = st.button("Generate output files", type="primary")
try:
    analyzer = NetflixTrendAnalyzer(csv_path)
    yearly = analyzer.yearly_releases()
    if run_export:
        analyzer.save_outputs()
        st.sidebar.success(f"Files saved in {OUTPUT_DIR}")
    min_year, max_year = int(yearly.release_year.min()), int(yearly.release_year.max())
    selected = st.slider("Release-year range", min_year, max_year, (min_year, max_year))
    view = yearly[yearly.release_year.between(*selected)]
    c1,c2,c3 = st.columns(3)
    c1.metric("Titles in selected period", f"{int(view.content_count.sum()):,}")
    c2.metric("Peak year", str(int(view.loc[view.content_count.idxmax(), "release_year"])) if not view.empty else "—")
    c3.metric("Average titles/year", f"{view.content_count.mean():,.1f}" if not view.empty else "—")
    st.plotly_chart(px.line(view, x="release_year", y="content_count", markers=True,
        title="Yearly content releases", labels={"release_year":"Release year","content_count":"Titles"}), use_container_width=True)
    st.plotly_chart(px.bar(view, x="release_year", y="growth_rate_pct", title="Year-over-year growth rate (%)",
        labels={"release_year":"Release year","growth_rate_pct":"Growth (%)"}), use_container_width=True)
    st.subheader("Yearly release table")
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.download_button("Download yearly analysis CSV", view.to_csv(index=False).encode("utf-8"),
                       "yearly_releases.csv", "text/csv")
    if not view.empty:
        peak = view.loc[view.content_count.idxmax()]
        st.info(f"Business insight: the highest-volume year in this selected range is {int(peak.release_year)} "
                f"with {int(peak.content_count):,} titles. Release-year counts describe title release dates, "
                "not Netflix acquisition or platform-addition dates.")
except Exception as exc:
    st.error(str(exc))
    st.write("Check that Task 1 has produced the cleaned CSV and that the path above is correct.")
