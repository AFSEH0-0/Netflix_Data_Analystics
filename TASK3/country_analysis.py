"""
Task 3 – Country-Wise Netflix Content Analysis
Input : TASK1/OUTPUT/netflix_cleaned.csv
Output: TASK3/OUTPUT/

Run from the project root:
    python TASK3/country_analysis.py
"""

from pathlib import Path
import re
import sys

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


class NetflixCountryAnalyzer:
    """Loads, cleans, analyzes, visualizes, and reports Netflix country data."""

    def __init__(self, input_file=None, output_dir=None):
        self.project_root = Path(__file__).resolve().parent.parent
        self.input_file = Path(input_file) if input_file else (
            self.project_root / "TASK1" / "OUTPUT" / "netflix_cleaned.csv"
        )
        self.output_dir = Path(output_dir) if output_dir else (
            self.project_root / "TASK3" / "OUTPUT"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.data = None
        self.country_data = None
        self.country_counts = None
        self.country_type_counts = None

        sns.set_theme(style="whitegrid")

    @staticmethod
    def find_column(data, possible_names):
        """Find a column without depending on capitalization or spaces."""
        normalized = {
            re.sub(r"[^a-z0-9]", "", str(column).lower()): column
            for column in data.columns
        }
        for name in possible_names:
            key = re.sub(r"[^a-z0-9]", "", name.lower())
            if key in normalized:
                return normalized[key]
        return None

    def load_data(self):
        if not self.input_file.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.input_file}\n"
                "Place netflix_cleaned.csv inside TASK1/OUTPUT/"
            )

        self.data = pd.read_csv(self.input_file)
        country_col = self.find_column(self.data, ["country", "countries"])
        if country_col is None:
            raise ValueError(
                "A 'country' column was not found in the cleaned dataset. "
                f"Available columns: {list(self.data.columns)}"
            )

        self.country_col = country_col
        self.type_col = self.find_column(self.data, ["type", "content_type"])
        self.id_col = self.find_column(self.data, ["show_id", "id"])

        print(f"[+] Loaded {len(self.data):,} Netflix records.")
        print(f"[+] Country column detected: {self.country_col}")

    @staticmethod
    def clean_country_name(value):
        if pd.isna(value):
            return None
        value = re.sub(r"\s+", " ", str(value)).strip()
        if not value or value.lower() in {"unknown", "not available", "n/a", "nan"}:
            return None
        return value

    def extract_countries(self):
        """Split multi-country records so every title is assigned to each country."""
        working = self.data.copy()

        if self.id_col:
            working["_content_id"] = working[self.id_col].astype(str)
        else:
            # A row number is used when the dataset has no title ID column.
            working["_content_id"] = working.index.astype(str)

        working["_country"] = working[self.country_col].apply(
            lambda value: (
                [self.clean_country_name(item) for item in str(value).split(",")]
                if pd.notna(value) else []
            )
        )

        self.country_data = working.explode("_country")
        self.country_data["_country"] = self.country_data["_country"].apply(
            self.clean_country_name
        )
        self.country_data = self.country_data.dropna(subset=["_country"])

        # A title is counted once per country, even if duplicate country names occur.
        self.country_data = self.country_data.drop_duplicates(
            subset=["_content_id", "_country"]
        )

        if self.type_col:
            self.country_data["_content_type"] = (
                self.country_data[self.type_col]
                .fillna("Unknown")
                .astype(str)
                .str.strip()
                .replace("", "Unknown")
            )
        else:
            self.country_data["_content_type"] = "Unknown"

        if self.country_data.empty:
            raise ValueError("No usable country values were found in the dataset.")

        print(f"[+] Extracted {self.country_data['_country'].nunique():,} countries.")
        print(f"[+] Country-title assignments: {len(self.country_data):,}")

    def analyze(self):
        self.country_counts = (
            self.country_data.groupby("_country")["_content_id"]
            .nunique()
            .sort_values(ascending=False)
            .rename("content_count")
            .reset_index()
            .rename(columns={"_country": "country"})
        )
        self.country_counts.insert(
            0, "rank", range(1, len(self.country_counts) + 1)
        )

        self.country_type_counts = (
            self.country_data.pivot_table(
                index="_country",
                columns="_content_type",
                values="_content_id",
                aggfunc="nunique",
                fill_value=0,
            )
            .reset_index()
            .rename(columns={"_country": "country"})
        )

        self.country_counts.to_csv(
            self.output_dir / "country_content_rankings.csv", index=False
        )
        self.country_type_counts.to_csv(
            self.output_dir / "country_content_by_type.csv", index=False
        )

        print("[+] Country rankings and content-type reports created.")

    def create_charts(self):
        top10 = self.country_counts.head(10).sort_values(
            "content_count", ascending=True
        )

        # Chart 1: Top 10 countries by total titles.
        plt.figure(figsize=(12, 7))
        sns.barplot(data=top10, x="content_count", y="country")
        plt.title("Top 10 Countries by Netflix Content")
        plt.xlabel("Number of Titles")
        plt.ylabel("Country")
        plt.tight_layout()
        plt.savefig(self.output_dir / "top_10_countries.png", dpi=300)
        plt.close()

        # Chart 2: Top 10 countries split by Movies and TV Shows.
        type_top = self.country_type_counts[
            self.country_type_counts["country"].isin(top10["country"])
        ].copy()
        type_columns = [
            column for column in type_top.columns if column != "country"
        ]
        if type_columns:
            type_top = type_top.set_index("country").reindex(
                top10["country"]
            ).fillna(0)
            type_top[type_columns].plot(
                kind="bar", stacked=True, figsize=(13, 7)
            )
            plt.title("Movies and TV Shows in the Top 10 Countries")
            plt.xlabel("Country")
            plt.ylabel("Number of Titles")
            plt.xticks(rotation=35, ha="right")
            plt.legend(title="Content Type")
            plt.tight_layout()
            plt.savefig(
                self.output_dir / "top_10_content_type_comparison.png",
                dpi=300,
            )
            plt.close()

        # Chart 3: Share of titles across the top 10 countries.
        pie_data = self.country_counts.head(10).copy()
        remaining = self.country_counts.iloc[10:]["content_count"].sum()
        if remaining > 0:
            pie_data = pd.concat(
                [
                    pie_data,
                    pd.DataFrame(
                        [{"country": "Other countries", "content_count": remaining}]
                    ),
                ],
                ignore_index=True,
            )

        plt.figure(figsize=(10, 8))
        plt.pie(
            pie_data["content_count"],
            labels=pie_data["country"],
            autopct="%1.1f%%",
            startangle=140,
        )
        plt.title("Netflix Content Distribution: Top 10 Countries vs Others")
        plt.tight_layout()
        plt.savefig(self.output_dir / "country_content_distribution.png", dpi=300)
        plt.close()

        # Chart 4: Top 15 country ranking.
        top15 = self.country_counts.head(15).sort_values(
            "content_count", ascending=True
        )
        plt.figure(figsize=(12, 8))
        sns.barplot(data=top15, x="content_count", y="country")
        plt.title("Top 15 Netflix Content-Producing Countries")
        plt.xlabel("Number of Titles")
        plt.ylabel("Country")
        plt.tight_layout()
        plt.savefig(self.output_dir / "top_15_countries.png", dpi=300)
        plt.close()

        print("[+] Four charts saved as PNG files.")

    def generate_business_insights(self):
        total_assignments = int(self.country_counts["content_count"].sum())
        total_countries = int(self.country_counts["country"].nunique())
        top = self.country_counts.head(10)
        leader = self.country_counts.iloc[0]
        top_three_total = int(top.head(3)["content_count"].sum())
        top_three_share = (
            (top_three_total / total_assignments) * 100
            if total_assignments else 0
        )

        lines = [
            "NETFLIX COUNTRY-WISE CONTENT ANALYSIS – BUSINESS INSIGHTS",
            "=" * 62,
            f"Countries represented in the dataset: {total_countries:,}",
            f"Total country-title assignments: {total_assignments:,}",
            "",
            "TOP-PRODUCING COUNTRY",
            f"{leader['country']} ranks first with "
            f"{int(leader['content_count']):,} title assignments.",
            "",
            "TOP 10 COUNTRY RANKING",
        ]

        for row in top.itertuples(index=False):
            lines.append(f"{row.rank}. {row.country}: {row.content_count:,} titles")

        lines.extend([
            "",
            "GEOGRAPHIC CONCENTRATION",
            f"The top three countries account for approximately "
            f"{top_three_share:.1f}% of all country-title assignments.",
            "",
            "BUSINESS INTERPRETATION",
            "- Countries with high title counts are major content markets "
            "or production hubs in this dataset.",
            "- Countries with lower counts may represent opportunities "
            "for localized content investment and licensing research.",
            "- Comparing Movies and TV Shows by country helps identify "
            "differences in content strategy across markets.",
            "- Multi-country titles are counted once for every listed country. "
            "Therefore, country counts are not mutually exclusive and their "
            "sum can exceed the number of unique Netflix titles.",
            "",
            "Note: These results describe the countries recorded in the dataset. "
            "They do not independently prove where a title was produced, "
            "how many viewers it has, or its commercial performance.",
        ])

        report = "\n".join(lines)
        (self.output_dir / "business_insights.txt").write_text(
            report, encoding="utf-8"
        )
        print("\n" + report)

    def run(self):
        print("\nNETFLIX COUNTRY-WISE CONTENT ANALYSIS")
        print("=" * 45)
        self.load_data()
        self.extract_countries()
        self.analyze()
        self.create_charts()
        self.generate_business_insights()
        print("\n[✓] TASK 3 COMPLETED")
        print(f"[+] All output files are saved in: {self.output_dir}")


if __name__ == "__main__":
    try:
        analyzer = NetflixCountryAnalyzer()
        analyzer.run()
    except Exception as error:
        print(f"\n[ERROR] {error}")
        sys.exit(1)
