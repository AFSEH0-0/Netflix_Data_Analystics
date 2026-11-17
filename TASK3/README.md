# Task 3 – Country-Wise Netflix Content Analysis

## Input dataset
Place the cleaned dataset at:

`TASK1/OUTPUT/netflix_cleaned.csv`

## Install dependencies

```bash
python -m pip install -r TASK3/requirements.txt
```

## Run

Run this command from the main project folder:

```bash
python TASK3/country_analysis.py
```

## Output

Generated files are saved in `TASK3/OUTPUT/`:

- `country_content_rankings.csv` – all countries ranked by title count
- `country_content_by_type.csv` – Movies/TV Shows counts per country
- `top_10_countries.png` – top 10 country chart
- `top_10_content_type_comparison.png` – stacked content-type chart
- `country_content_distribution.png` – top 10 vs other countries pie chart
- `top_15_countries.png` – top 15 country chart
- `business_insights.txt` – automatically generated findings

## Counting method

If a title lists multiple countries, it is assigned once to each listed country.
The country totals are therefore country-title assignments, not mutually
exclusive global title totals.
