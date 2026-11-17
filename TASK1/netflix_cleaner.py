import pandas as pd
import numpy as np

from pathlib import Path
from datetime import datetime


class NetflixDataCleaner:

    def __init__(self, input_file, output_folder):

        self.input_file = Path(input_file)
        self.output_folder = Path(output_folder)

        self.output_folder.mkdir(parents=True, exist_ok=True)

        self.cleaned_file = self.output_folder / "netflix_cleaned.csv"
        self.report_file = self.output_folder / "cleaning_report.txt"

        self.df = None

        self.original_rows = 0
        self.duplicates_removed = 0
        self.missing_values_handled = 0
        self.invalid_dates = 0
        self.missing_values_before = {}
        self.missing_values_after = {}

    # --------------------------------------------------
    # STEP 1: IMPORT DATASET
    # --------------------------------------------------

    def import_dataset(self):

        print("\n[STEP 1] Importing Netflix Dataset...")

        if not self.input_file.exists():
            raise FileNotFoundError(
                f"Dataset not found: {self.input_file}"
            )

        self.df = pd.read_csv(
            self.input_file,
            encoding="utf-8-sig",
            low_memory=False
        )

        self.original_rows = len(self.df)

        print("[SUCCESS] Dataset imported successfully.")
        print(f"Total Records: {len(self.df)}")
        print(f"Total Columns: {len(self.df.columns)}")

        print("\nDataset Columns:")
        print(list(self.df.columns))

        return self.df

    # --------------------------------------------------
    # STEP 2: STANDARDIZE COLUMN NAMES
    # --------------------------------------------------

    def standardize_column_names(self):

        print("\n[STEP 2] Standardizing Column Names...")

        self.df.columns = (
            self.df.columns
            .str.strip()
            .str.lower()
            .str.replace(r"[^a-z0-9]+", "_", regex=True)
            .str.strip("_")
        )

        print("[SUCCESS] Column names standardized.")

    # --------------------------------------------------
    # STEP 3: HANDLE MISSING VALUES
    # --------------------------------------------------

    def handle_missing_values(self):

        print("\n[STEP 3] Identifying and Handling Missing Values...")

        # Convert common empty-value representations to NaN.
        null_values = [
            "",
            " ",
            "NA",
            "N/A",
            "NULL",
            "null",
            "None",
            "none",
            "NaN",
            "nan"
        ]

        for column in self.df.select_dtypes(include=["object", "string"]).columns:

            self.df[column] = (
                self.df[column]
                .astype("string")
                .str.strip()
                .replace(null_values, pd.NA)
            )

        # Record missing values before cleaning.
        self.missing_values_before = (
            self.df.isnull().sum().to_dict()
        )

        print("\nMissing Values Before Cleaning:")

        for column, count in self.missing_values_before.items():

            if count > 0:
                print(f"{column}: {count}")

        # Remove records without a title because they cannot
        # be reliably identified in business reports.
        if "title" in self.df.columns:

            before = len(self.df)

            self.df = self.df.dropna(subset=["title"])

            removed = before - len(self.df)

            print(f"\nRecords removed due to missing title: {removed}")

        # Fill missing values in descriptive columns.
        fill_columns = [
            "director",
            "cast",
            "country",
            "rating",
            "duration",
            "listed_in",
            "description"
        ]

        for column in fill_columns:

            if column in self.df.columns:

                missing_count = self.df[column].isna().sum()

                self.df[column] = self.df[column].fillna("Unknown")

                self.missing_values_handled += int(missing_count)

        # Handle missing Type separately.
        if "type" in self.df.columns:

            missing_count = self.df["type"].isna().sum()

            self.df["type"] = self.df["type"].fillna("Unknown")

            self.missing_values_handled += int(missing_count)

        # Convert missing release years to pandas nullable integers.
        if "release_year" in self.df.columns:

            self.df["release_year"] = pd.to_numeric(
                self.df["release_year"],
                errors="coerce"
            ).astype("Int64")

        # date_added is kept missing if unavailable.
        # An invented date would corrupt time-based analysis.

        self.missing_values_after = (
            self.df.isnull().sum().to_dict()
        )

        print("\n[SUCCESS] Missing-value handling completed.")

    # --------------------------------------------------
    # STEP 4: REMOVE DUPLICATE RECORDS
    # --------------------------------------------------

    def remove_duplicates(self):

        print("\n[STEP 4] Removing Duplicate Records...")

        before = len(self.df)

        # Remove completely identical records.
        self.df = self.df.drop_duplicates()

        exact_duplicates = before - len(self.df)

        # Remove repeated Netflix show IDs if available.
        # Keep the first occurrence.
        id_duplicates = 0

        if "show_id" in self.df.columns:

            before_id = len(self.df)

            self.df = self.df.drop_duplicates(
                subset=["show_id"],
                keep="first"
            )

            id_duplicates = before_id - len(self.df)

        self.duplicates_removed = (
            exact_duplicates + id_duplicates
        )

        print(f"Exact duplicates removed: {exact_duplicates}")
        print(f"Duplicate show IDs removed: {id_duplicates}")

        print("[SUCCESS] Duplicate removal completed.")

    # --------------------------------------------------
    # STEP 5: CLEAN FORMATTING INCONSISTENCIES
    # --------------------------------------------------

    def clean_formatting(self):

        print("\n[STEP 5] Cleaning Formatting Inconsistencies...")

        for column in self.df.select_dtypes(
            include=["object", "string"]
        ).columns:

            self.df[column] = (
                self.df[column]
                .astype("string")
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
            )

        # Standardize show IDs.
        if "show_id" in self.df.columns:

            self.df["show_id"] = (
                self.df["show_id"]
                .str.upper()
            )

        # Standardize country names.
        if "country" in self.df.columns:

            self.df["country"] = self.df["country"].apply(
                self.standardize_country
            )

        # Standardize movie and TV show types.
        if "type" in self.df.columns:

            self.df["type"] = self.df["type"].apply(
                self.standardize_type
            )

        # Standardize content ratings.
        if "rating" in self.df.columns:

            self.df["rating"] = self.df["rating"].apply(
                self.standardize_rating
            )

        # Standardize duration formatting.
        if "duration" in self.df.columns:

            self.df["duration"] = self.df["duration"].apply(
                self.standardize_duration
            )

        # Standardize title and description formatting.
        for column in ["title", "director", "cast", "listed_in"]:

            if column in self.df.columns:

                self.df[column] = (
                    self.df[column]
                    .str.strip()
                )

        print("[SUCCESS] Formatting inconsistencies corrected.")

    # --------------------------------------------------
    # COUNTRY STANDARDIZATION
    # --------------------------------------------------

    @staticmethod
    def standardize_country(value):

        if pd.isna(value) or value == "Unknown":
            return value

        countries = value.split(",")

        cleaned_countries = []

        for country in countries:

            country = country.strip()

            if not country:
                continue

            # Correct common country-name variations.
            country_aliases = {
                "usa": "United States",
                "u.s.a.": "United States",
                "us": "United States",
                "uk": "United Kingdom",
                "u.k.": "United Kingdom",
                "south korea": "South Korea",
                "north korea": "North Korea"
            }

            normalized = country.lower()

            country = country_aliases.get(
                normalized,
                country.title()
            )

            cleaned_countries.append(country)

        # Remove repeated countries while preserving order.
        return ", ".join(dict.fromkeys(cleaned_countries))

    # --------------------------------------------------
    # TYPE STANDARDIZATION
    # --------------------------------------------------

    @staticmethod
    def standardize_type(value):

        if pd.isna(value) or value == "Unknown":
            return value

        value = value.strip().lower()

        type_mapping = {
            "movie": "Movie",
            "movies": "Movie",
            "film": "Movie",
            "films": "Movie",
            "tv show": "TV Show",
            "tv shows": "TV Show",
            "tvshow": "TV Show",
            "tv_show": "TV Show",
            "series": "TV Show",
            "television show": "TV Show"
        }

        return type_mapping.get(value, value.title())

    # --------------------------------------------------
    # RATING STANDARDIZATION
    # --------------------------------------------------

    @staticmethod
    def standardize_rating(value):

        if pd.isna(value) or value == "Unknown":
            return value

        value = value.strip().upper()

        # Correct common spacing and punctuation differences.
        value = value.replace(" ", "")

        rating_mapping = {
            "TVMA": "TV-MA",
            "TV14": "TV-14",
            "TVPG": "TV-PG",
            "TVY7": "TV-Y7",
            "TVY7FV": "TV-Y7-FV",
            "TVY": "TV-Y",
            "TVG": "TV-G",
            "G": "G",
            "PG": "PG",
            "PG13": "PG-13",
            "R": "R",
            "NC17": "NC-17",
            "NR": "NR",
            "UR": "UR",
            "TV-NR": "TV-NR",
            "TV-NR ": "TV-NR"
        }

        return rating_mapping.get(value, value)

    # --------------------------------------------------
    # DURATION STANDARDIZATION
    # --------------------------------------------------

    @staticmethod
    def standardize_duration(value):

        if pd.isna(value) or value == "Unknown":
            return value

        value = value.strip().lower()

        value = value.replace("mins", "min")
        value = value.replace("minutes", "min")
        value = value.replace("seasons", "season")

        return value

    # --------------------------------------------------
    # STEP 6: STANDARDIZE DATE FORMAT
    # --------------------------------------------------

    def standardize_dates(self):

        print("\n[STEP 6] Standardizing Date Formats...")

        if "date_added" not in self.df.columns:

            print("[INFO] date_added column not found.")
            return

        before = self.df["date_added"].notna().sum()

        self.df["date_added"] = pd.to_datetime(
            self.df["date_added"],
            errors="coerce"
        )

        after = self.df["date_added"].notna().sum()

        self.invalid_dates = int(before - after)

        # Export dates in a consistent YYYY-MM-DD format.
        self.df["date_added"] = (
            self.df["date_added"]
            .dt.strftime("%Y-%m-%d")
        )

        self.df["date_added"] = (
            self.df["date_added"].fillna("Unknown")
        )

        print(f"Invalid dates converted to Unknown: {self.invalid_dates}")
        print("[SUCCESS] Date formatting completed.")

    # --------------------------------------------------
    # STEP 7: EXPORT CLEANED DATASET
    # --------------------------------------------------

    def export_dataset(self):

        print("\n[STEP 7] Exporting Cleaned Dataset...")

        self.df.to_csv(
            self.cleaned_file,
            index=False,
            encoding="utf-8-sig"
        )

        print(f"[SUCCESS] Cleaned dataset saved to: {self.cleaned_file}")

    # --------------------------------------------------
    # STEP 8: GENERATE CLEANING REPORT
    # --------------------------------------------------

    def generate_report(self):

        print("\n[STEP 8] Generating Cleaning Report...")

        report = []

        report.append("=" * 55)
        report.append("       NETFLIX DATA CLEANING REPORT")
        report.append("=" * 55)

        report.append(
            f"\nGenerated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        report.append(f"Input Dataset: {self.input_file}")

        report.append("\n--- DATASET INFORMATION ---")

        report.append(f"Original Records: {self.original_rows}")

        report.append(f"Final Records: {len(self.df)}")

        report.append(f"Total Columns: {len(self.df.columns)}")

        report.append(
            f"Records Removed: {self.original_rows - len(self.df)}"
        )

        report.append("\n--- MISSING VALUES ---")

        report.append("Missing values before cleaning:")

        for column, count in self.missing_values_before.items():

            report.append(f"{column}: {count}")

        report.append(
            f"\nMissing values filled: {self.missing_values_handled}"
        )

        report.append("\nRemaining missing values:")

        for column, count in self.missing_values_after.items():

            report.append(f"{column}: {count}")

        report.append("\n--- DUPLICATE RECORDS ---")

        report.append(
            f"Duplicates Removed: {self.duplicates_removed}"
        )

        report.append("\n--- DATE CLEANING ---")

        report.append(
            f"Invalid Dates: {self.invalid_dates}"
        )

        report.append("\n--- FINAL DATASET ---")

        report.append(
            f"Movie Records: {(self.df['type'] == 'Movie').sum()}"
            if "type" in self.df.columns else "Type column unavailable"
        )

        report.append(
            f"TV Show Records: {(self.df['type'] == 'TV Show').sum()}"
            if "type" in self.df.columns else ""
        )

        report.append("\nColumn Names:")

        report.extend(self.df.columns.tolist())

        report.append("\n" + "=" * 55)
        report.append("           CLEANING COMPLETED")
        report.append("=" * 55)

        with open(self.report_file, "w", encoding="utf-8") as file:

            file.write("\n".join(report))

        print(f"[SUCCESS] Report saved to: {self.report_file}")

    # --------------------------------------------------
    # DISPLAY FINAL SUMMARY
    # --------------------------------------------------

    def display_summary(self):

        print("\n" + "=" * 55)
        print("          NETFLIX DATA CLEANING SUMMARY")
        print("=" * 55)

        print(f"Original Records       : {self.original_rows}")
        print(f"Final Records          : {len(self.df)}")
        print(f"Total Columns          : {len(self.df.columns)}")
        print(f"Duplicates Removed     : {self.duplicates_removed}")
        print(f"Missing Values Filled  : {self.missing_values_handled}")
        print(f"Invalid Dates          : {self.invalid_dates}")

        print("\nFinal Dataset Preview:")

        print(self.df.head(5).to_string(index=False))

        print("\nOutput Files:")
        print(f"1. {self.cleaned_file}")
        print(f"2. {self.report_file}")

        print("\n[COMPLETED] All cleaning operations finished.")

    # --------------------------------------------------
    # MAIN EXECUTION METHOD
    # --------------------------------------------------

    def run(self):

        try:

            self.import_dataset()

            self.standardize_column_names()

            self.handle_missing_values()

            self.remove_duplicates()

            self.clean_formatting()

            self.standardize_dates()

            self.export_dataset()

            self.generate_report()

            self.display_summary()

        except FileNotFoundError as error:

            print(f"\n[ERROR] {error}")

        except pd.errors.EmptyDataError:

            print("\n[ERROR] The CSV dataset is empty.")

        except pd.errors.ParserError as error:

            print(f"\n[ERROR] CSV parsing failed: {error}")

        except Exception as error:

            print(f"\n[ERROR] Unexpected error: {error}")


# ======================================================
# PROGRAM ENTRY POINT
# ======================================================

if __name__ == "__main__":

    cleaner = NetflixDataCleaner(
        input_file="DATASET/dataset.csv",
        output_folder="TASK1/OUTPUT"
    )

    cleaner.run()