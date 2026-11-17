# Task 2 — Netflix Content Type Analysis Dashboard

Object-oriented Python project that analyzes the distribution of Movies and TV Shows.

## Project structure

```text
TASK2/
├── main.py
├── content_analyzer.py
├── dashboard.py
├── requirements.txt
├── README.md
└── OUTPUT/
    └── .gitkeep
```

## Dataset

By default, the project looks for:

```text
TASK1/OUTPUT/netflix_cleaned.csv
```

The path is relative to the parent directory of `TASK2`. If your Task 1 output uses another filename or location, update `default_csv` in `main.py`.

You can also upload the cleaned CSV directly in the Streamlit dashboard.

The CSV must contain a `type` column. Accepted values include `Movie`, `Movies`, `TV Show`, and `TV Shows` (case and surrounding whitespace are normalized).

## Run on Windows, Linux, or Kali

From the directory containing `TASK2`:

```bash
python -m venv venv
```

Activate it:

Linux / Kali:
```bash
source venv/bin/activate
```

Windows:
```powershell
venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r TASK2/requirements.txt
```

Start the dashboard:
```bash
streamlit run TASK2/main.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`.

## Generated files

The dashboard creates these files inside `TASK2/OUTPUT/`:

- `content_distribution_bar.png` — title counts by content type.
- `content_distribution_pie.png` — percentage share by content type.
- `content_type_metrics.csv` — counts and percentages.
- `summary_report.txt` — generated findings and summary.

## OOP design

- `NetflixContentAnalyzer` owns dataset loading, normalization, calculations, chart generation, and report export.
- `NetflixDashboard` owns the Streamlit presentation and calls the analyzer methods.

All counts and percentages are calculated from the loaded cleaned dataset; no dataset totals are hardcoded.
