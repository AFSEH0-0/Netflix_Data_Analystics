from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

TASK_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = TASK_DIR / "OUTPUT"
OUTPUT_DIR.mkdir(exist_ok=True)
DEFAULT_DATA = Path(r"D:\MY DATA\PROGRAMMING\Auspify\TASK1\OUTPUT\netflix_cleaned.csv")

class NetflixBusinessAnalyzer:
    def __init__(self, csv_path):
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Cleaned dataset not found: {path}")
        self.df = pd.read_csv(path)
        required = {"type", "release_year", "rating", "listed_in", "country"}
        missing = required - set(self.df.columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
        self.df["release_year"] = pd.to_numeric(self.df["release_year"], errors="coerce")
        for col in ["type", "rating", "listed_in", "country"]:
            self.df[col] = self.df[col].fillna("Unknown").astype(str).str.strip()

    def profile(self):
        return {
            "total_titles": len(self.df),
            "movies": int(self.df.type.eq("Movie").sum()),
            "tv_shows": int(self.df.type.eq("TV Show").sum()),
            "unique_release_years": int(self.df.release_year.nunique()),
            "missing_release_year": int(self.df.release_year.isna().sum()),
            "unique_ratings": int(self.df.rating.nunique())
        }

    def yearly(self):
        return self.df.dropna(subset=["release_year"]).groupby("release_year").size().reset_index(name="titles").sort_values("release_year")

    def top_values(self, column, split=False, limit=15):
        frame = self.df[[column]].copy()
        if split:
            frame[column] = frame[column].str.split(",")
            frame = frame.explode(column)
            frame[column] = frame[column].str.strip()
        frame = frame[frame[column].ne("") & frame[column].ne("Unknown")]
        return frame[column].value_counts().head(limit).rename_axis(column).reset_index(name="titles")

    def save_report(self):
        profile = self.profile()
        yearly = self.yearly()
        ratings = self.top_values("rating", limit=30)
        genres = self.top_values("listed_in", split=True, limit=30)
        countries = self.top_values("country", split=True, limit=20)
        yearly.to_csv(OUTPUT_DIR / "yearly_trends.csv", index=False)
        ratings.to_csv(OUTPUT_DIR / "rating_distribution.csv", index=False)
        genres.to_csv(OUTPUT_DIR / "top_genres.csv", index=False)
        countries.to_csv(OUTPUT_DIR / "top_countries.csv", index=False)
        lines = [
            "NETFLIX BUSINESS INSIGHTS REPORT",
            "=" * 34,
            f"Total titles: {profile['total_titles']:,}",
            f"Movies: {profile['movies']:,}",
            f"TV Shows: {profile['tv_shows']:,}",
            f"Distinct release years: {profile['unique_release_years']:,}",
            f"Records without release year: {profile['missing_release_year']:,}",
            f"Distinct rating labels: {profile['unique_ratings']:,}",
            "",
            "KEY OBSERVATIONS",
            f"- Content mix: Movies are {profile['movies']/profile['total_titles']*100:.1f}% of all titles." if profile["total_titles"] else "- No records available.",
            f"- Most common rating: {ratings.iloc[0][ 'rating' ]} ({int(ratings.iloc[0]['titles']):,} titles)." if not ratings.empty else "- No rating data.",
            f"- Leading genre: {genres.iloc[0]['listed_in']} ({int(genres.iloc[0]['titles']):,} titles)." if not genres.empty else "- No genre data.",
            f"- Leading country label: {countries.iloc[0]['country']} ({int(countries.iloc[0]['titles']):,} titles)." if not countries.empty else "- No country data.",
            "",
            "INTERPRETATION LIMITATIONS",
            "- Release year is not the same as the date a title was added to Netflix.",
            "- Ratings are content classifications, not measured viewer demographics.",
            "- Country and genre values can contain multiple comma-separated labels per title.",
            "- These are descriptive dataset findings, not causal explanations or subscriber-performance metrics."
        ]
        report = "\n".join(lines)
        (OUTPUT_DIR / "business_insights_report.txt").write_text(report, encoding="utf-8")
        return profile, yearly, ratings, genres, countries, report

st.set_page_config(page_title="Task 6 | Business Insights", layout="wide")
st.title("Task 6 — Netflix Business Insights Report")
st.caption("Executive overview, exploratory analysis, interactive dashboards and downloadable reporting.")
with st.sidebar:
    st.header("Dataset")
    csv_path = st.text_input("Cleaned CSV path", str(DEFAULT_DATA))
    generate = st.button("Generate full report", type="primary")
try:
    analyzer = NetflixBusinessAnalyzer(csv_path)
    profile, yearly, ratings, genres, countries, report = analyzer.save_report()
    if generate:
        st.sidebar.success(f"Report and CSV files saved in {OUTPUT_DIR}")
    a,b,c,d = st.columns(4)
    a.metric("Total titles", f"{profile['total_titles']:,}")
    b.metric("Movies", f"{profile['movies']:,}")
    c.metric("TV Shows", f"{profile['tv_shows']:,}")
    d.metric("Release years", f"{profile['unique_release_years']:,}")
    tab1,tab2,tab3,tab4 = st.tabs(["Content overview","Trends","Audience & genres","Geography & report"])
    with tab1:
        type_counts = analyzer.df.type.value_counts().rename_axis("type").reset_index(name="titles")
        col1,col2 = st.columns(2)
        col1.plotly_chart(px.pie(type_counts, names="type", values="titles", title="Movies vs TV Shows"), use_container_width=True)
        col2.plotly_chart(px.bar(ratings.head(15), x="rating", y="titles", title="Top rating categories"), use_container_width=True)
    with tab2:
        st.plotly_chart(px.line(yearly, x="release_year", y="titles", markers=True, title="Titles by release year"), use_container_width=True)
        if not yearly.empty:
            peak = yearly.loc[yearly.titles.idxmax()]
            st.write(f"Highest release-year count: **{int(peak.release_year)}** ({int(peak.titles):,} titles).")
    with tab3:
        top_genres = genres.head(15)
        st.plotly_chart(px.bar(top_genres.sort_values("titles"), x="titles", y="listed_in", orientation="h",
            title="Most common genres"), use_container_width=True)
    with tab4:
        st.plotly_chart(px.bar(countries.head(15).sort_values("titles"), x="titles", y="country", orientation="h",
            title="Most frequent country labels"), use_container_width=True)
        st.text_area("Executive report", report, height=360)
        st.download_button("Download business insights report", report, "business_insights_report.txt", "text/plain")
    st.subheader("Export analysis tables")
    exports = {
        "yearly_trends.csv": yearly,
        "rating_distribution.csv": ratings,
        "top_genres.csv": genres,
        "top_countries.csv": countries
    }
    cols = st.columns(4)
    for (filename, frame), col in zip(exports.items(), cols):
        col.download_button(f"Download {filename}", frame.to_csv(index=False).encode("utf-8"), filename, "text/csv")
except Exception as exc:
    st.error(str(exc))
    st.write("Check the cleaned CSV path and ensure Task 1 includes type, release_year, rating, listed_in and country.")
