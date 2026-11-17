from pathlib import Path
import streamlit as st
from content_analyzer import NetflixContentAnalyzer


class NetflixDashboard:
    """Streamlit interface for the Netflix content analysis."""

    def __init__(self, analyzer):
        self.analyzer = analyzer
        self.output_dir = Path(__file__).resolve().parent / "OUTPUT"

    def run(self):
        st.set_page_config(
            page_title="Netflix Content Type Analysis",
            page_icon="",
            layout="wide"
        )
        st.title("Netflix Content Type Analysis Dashboard")
        st.caption("Movie and TV Show distribution from the cleaned Netflix dataset.")

        uploaded = st.file_uploader("Upload cleaned Netflix CSV", type=["csv"])

        try:
            self.analyzer.load_data(uploaded_file=uploaded)
            result = self.analyzer.analyze()
            chart_paths = self.analyzer.create_charts(self.output_dir)
            report_path, report_text = self.analyzer.create_summary(self.output_dir)
            metrics_path = self.analyzer.export_metrics(self.output_dir)

            st.subheader("Dataset overview")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Titles", f"{result['total']:,}")
            col2.metric("Movies", f"{result['movie_count']:,}", f"{result['movie_percentage']:.2f}%")
            col3.metric("TV Shows", f"{result['tv_show_count']:,}", f"{result['tv_show_percentage']:.2f}%")

            st.subheader("Content distribution")
            left, right = st.columns(2)
            with left:
                st.image(str(chart_paths[0]), caption="Number of titles by content type", use_container_width=True)
            with right:
                st.image(str(chart_paths[1]), caption="Percentage of each content type", use_container_width=True)

            st.subheader("Comparison")
            comparison = {
                "Content Type": ["Movies", "TV Shows"],
                "Count": [result["movie_count"], result["tv_show_count"]],
                "Share (%)": [result["movie_percentage"], result["tv_show_percentage"]],
            }
            st.dataframe(comparison, hide_index=True, use_container_width=True)

            st.subheader("Key findings")
            if result["movie_count"] > result["tv_show_count"]:
                st.write(
                    f"Movies are the dominant content type, exceeding TV Shows by "
                    f"{result['movie_count'] - result['tv_show_count']:,} titles."
                )
            elif result["tv_show_count"] > result["movie_count"]:
                st.write(
                    f"TV Shows are the dominant content type, exceeding Movies by "
                    f"{result['tv_show_count'] - result['movie_count']:,} titles."
                )
            else:
                st.write("Movies and TV Shows have equal representation.")

            with st.expander("Full summary report"):
                st.code(report_text, language="text")

            st.subheader("Output files")
            st.write(f"Saved to: `{self.output_dir}`")
            for path in [*chart_paths, report_path, metrics_path]:
                st.write(f"- `{path.name}`")

            st.download_button(
                "Download summary report",
                data=report_path.read_text(encoding="utf-8"),
                file_name="summary_report.txt",
                mime="text/plain"
            )
            st.download_button(
                "Download metrics CSV",
                data=metrics_path.read_bytes(),
                file_name="content_type_metrics.csv",
                mime="text/csv"
            )

        except Exception as error:
            st.error(str(error))
            st.info(
                "Expected input: a cleaned Netflix CSV containing a column named 'type' "
                "with values such as 'Movie' and 'TV Show'."
            )
