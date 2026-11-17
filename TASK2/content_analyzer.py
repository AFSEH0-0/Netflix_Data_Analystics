from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class NetflixContentAnalyzer:
    """Loads Netflix data and calculates Movie/TV Show distribution."""

    REQUIRED_COLUMN = "type"

    def __init__(self, dataset_path):
        self.dataset_path = Path(dataset_path)
        self.data = None
        self.counts = None
        self.proportions = None

    def load_data(self, uploaded_file=None):
        """Load a CSV from disk or from a Streamlit uploaded file."""
        source = uploaded_file if uploaded_file is not None else self.dataset_path

        if uploaded_file is None and not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.dataset_path}. "
                "Place the cleaned CSV there or upload it in the dashboard."
            )

        self.data = pd.read_csv(source)
        self.data.columns = self.data.columns.str.strip().str.lower()

        if self.REQUIRED_COLUMN not in self.data.columns:
            raise ValueError(
                "The dataset must contain a 'type' column with Movie and TV Show values."
            )

        self.data[self.REQUIRED_COLUMN] = (
            self.data[self.REQUIRED_COLUMN]
            .astype("string")
            .str.strip()
            .str.lower()
            .replace({
                "movies": "movie",
                "tv shows": "tv show",
                "tv-show": "tv show",
                "tvshow": "tv show",
            })
        )

        self.data = self.data[
            self.data[self.REQUIRED_COLUMN].isin(["movie", "tv show"])
        ].copy()

        if self.data.empty:
            raise ValueError("No valid Movie or TV Show records were found.")

        return self.data

    def analyze(self):
        if self.data is None:
            self.load_data()

        self.counts = (
            self.data[self.REQUIRED_COLUMN]
            .value_counts()
            .reindex(["movie", "tv show"], fill_value=0)
        )

        total = int(self.counts.sum())
        self.proportions = (self.counts / total * 100).round(2)

        return {
            "total": total,
            "counts": self.counts,
            "proportions": self.proportions,
            "movie_count": int(self.counts["movie"]),
            "tv_show_count": int(self.counts["tv show"]),
            "movie_percentage": float(self.proportions["movie"]),
            "tv_show_percentage": float(self.proportions["tv show"]),
        }

    def create_charts(self, output_dir):
        """Create and save bar and pie charts."""
        if self.counts is None:
            self.analyze()

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        labels = ["Movies", "TV Shows"]
        values = [int(self.counts["movie"]), int(self.counts["tv show"])]
        percentages = [float(self.proportions["movie"]), float(self.proportions["tv show"])]

        sns.set_theme(style="whitegrid")

        fig, ax = plt.subplots(figsize=(8, 5))
        bars = sns.barplot(x=labels, y=values, ax=ax)
        ax.set_title("Netflix Content Type Distribution")
        ax.set_xlabel("Content Type")
        ax.set_ylabel("Number of Titles")
        for bar, value in zip(bars.patches, values):
            ax.annotate(
                f"{value:,}",
                (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                ha="center", va="bottom", xytext=(0, 5),
                textcoords="offset points"
            )
        fig.tight_layout()
        fig.savefig(output_dir / "content_distribution_bar.png", dpi=160)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(7, 7))
        ax.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"edgecolor": "white", "linewidth": 1}
        )
        ax.set_title("Movies vs TV Shows — Percentage")
        fig.tight_layout()
        fig.savefig(output_dir / "content_distribution_pie.png", dpi=160)
        plt.close(fig)

        return [
            output_dir / "content_distribution_bar.png",
            output_dir / "content_distribution_pie.png",
        ]

    def create_summary(self, output_dir):
        result = self.analyze()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if result["movie_count"] > result["tv_show_count"]:
            dominant = "Movies"
            difference = result["movie_count"] - result["tv_show_count"]
        elif result["tv_show_count"] > result["movie_count"]:
            dominant = "TV Shows"
            difference = result["tv_show_count"] - result["movie_count"]
        else:
            dominant = "Both categories are equally represented"
            difference = 0

        lines = [
            "NETFLIX CONTENT TYPE ANALYSIS",
            "=" * 36,
            f"Total titles analyzed: {result['total']:,}",
            f"Movies: {result['movie_count']:,} ({result['movie_percentage']:.2f}%)",
            f"TV Shows: {result['tv_show_count']:,} ({result['tv_show_percentage']:.2f}%)",
            "",
            f"Dominant content type: {dominant}",
        ]

        if difference:
            lines.append(f"Count difference: {difference:,} titles")

        lines += [
            "",
            "KEY FINDING",
            f"{dominant} represent the larger share of the dataset."
            if difference else "Movies and TV Shows have the same count.",
            "",
            "Note: Results describe the supplied cleaned dataset only.",
        ]

        report_path = output_dir / "summary_report.txt"
        report_path.write_text("\n".join(lines), encoding="utf-8")
        return report_path, "\n".join(lines)

    def export_metrics(self, output_dir):
        result = self.analyze()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        metrics = pd.DataFrame({
            "content_type": ["Movie", "TV Show"],
            "count": [result["movie_count"], result["tv_show_count"]],
            "percentage": [result["movie_percentage"], result["tv_show_percentage"]],
        })
        path = output_dir / "content_type_metrics.csv"
        metrics.to_csv(path, index=False)
        return path
