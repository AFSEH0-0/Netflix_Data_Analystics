from pathlib import Path
import pandas as pd
import streamlit as st
import plotly.express as px

TASK_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = TASK_DIR / "OUTPUT"
OUTPUT_DIR.mkdir(exist_ok=True)
DEFAULT_DATA = Path(r"D:\MY DATA\PROGRAMMING\Auspify\TASK1\OUTPUT\netflix_cleaned.csv")

class NetflixAudienceAnalyzer:
    def __init__(self, csv_path):
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"Cleaned dataset not found: {path}")
        self.df = pd.read_csv(path)
        required = {"rating", "listed_in", "type"}
        missing = required - set(self.df.columns)
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
        for col in required:
            self.df[col] = self.df[col].fillna("Unknown").astype(str).str.strip()
        self.df.loc[self.df["rating"].eq(""), "rating"] = "Unknown"
        self.df.loc[self.df["listed_in"].eq(""), "listed_in"] = "Unknown"

    def rating_counts(self):
        return self.df.groupby(["rating", "type"]).size().reset_index(name="titles")

    def genre_counts(self):
        genres = self.df[["type", "listed_in"]].copy()
        genres["genre"] = genres["listed_in"].str.split(",")
        genres = genres.explode("genre")
        genres["genre"] = genres["genre"].str.strip()
        genres = genres[genres["genre"].ne("") & genres["genre"].ne("Unknown")]
        return genres.groupby(["genre", "type"]).size().reset_index(name="titles").sort_values("titles", ascending=False)

    def save_outputs(self):
        ratings = self.rating_counts()
        genres = self.genre_counts()
        ratings.to_csv(OUTPUT_DIR / "rating_by_content_type.csv", index=False)
        genres.to_csv(OUTPUT_DIR / "genre_by_content_type.csv", index=False)
        ratings.pivot(index="rating", columns="type", values="titles").fillna(0).to_csv(OUTPUT_DIR / "rating_comparison.csv")
        top = genres.groupby("genre")["titles"].sum().sort_values(ascending=False).head(10)
        (OUTPUT_DIR / "audience_insights.txt").write_text(
            "Top genres:\n" + top.to_string() +
            "\n\nRatings are content classifications, not measured viewer age or demographic data.\n",
            encoding="utf-8")
        return ratings, genres

st.set_page_config(page_title="Task 5 | Ratings & Genres", layout="wide")
st.title("Task 5 — Content Rating & Genre Analysis")
st.caption("Compare rating classifications and genre mix across Movies and TV Shows.")
with st.sidebar:
    st.header("Dataset")
    csv_path = st.text_input("Cleaned CSV path", str(DEFAULT_DATA))
    export = st.button("Generate output files", type="primary")
try:
    analyzer = NetflixAudienceAnalyzer(csv_path)
    ratings, genres = analyzer.save_outputs() if export else (analyzer.rating_counts(), analyzer.genre_counts())
    if export:
        st.sidebar.success(f"Files saved in {OUTPUT_DIR}")
    content_types = sorted(analyzer.df["type"].unique().tolist())
    selected_types = st.multiselect("Content type", content_types, default=content_types)
    rating_view = ratings[ratings.type.isin(selected_types)]
    genre_view = genres[genres.type.isin(selected_types)]
    top_n = st.slider("Number of genres to display", 5, 30, 15)
    left,right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(rating_view, x="rating", y="titles", color="type", barmode="group",
            title="Content ratings by type", labels={"rating":"Rating","titles":"Titles","type":"Content type"}),
            use_container_width=True)
    with right:
        top_genres = genre_view.groupby("genre", as_index=False)["titles"].sum().nlargest(top_n, "titles")
        st.plotly_chart(px.bar(top_genres.sort_values("titles"), x="titles", y="genre", orientation="h",
            title=f"Top {top_n} genres", labels={"titles":"Titles","genre":"Genre"}), use_container_width=True)
    st.subheader("Genre comparison by content type")
    st.plotly_chart(px.bar(genre_view[genre_view.genre.isin(top_genres.genre)], x="genre", y="titles",
        color="type", barmode="group", title="Top genres: Movies vs TV Shows"), use_container_width=True)
    st.subheader("Detailed data")
    tab1,tab2 = st.tabs(["Ratings","Genres"])
    with tab1:
        st.dataframe(rating_view, use_container_width=True, hide_index=True)
        st.download_button("Download ratings CSV", rating_view.to_csv(index=False).encode(), "rating_analysis.csv", "text/csv")
    with tab2:
        st.dataframe(genre_view, use_container_width=True, hide_index=True)
        st.download_button("Download genres CSV", genre_view.to_csv(index=False).encode(), "genre_analysis.csv", "text/csv")
    if not top_genres.empty:
        st.info(f"Insight: the most represented genre in the current selection is "
                f"{top_genres.iloc[0]['genre']} ({int(top_genres.iloc[0]['titles']):,} titles). "
                "Ratings indicate content classification; they do not reveal actual audience demographics.")
except Exception as exc:
    st.error(str(exc))
    st.write("Confirm the Task 1 cleaned CSV path and required columns: rating, listed_in, type.")
