# Netflix Content Rating and Genre Analysis

## Requirements
Python 3.10 or newer. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Dataset
Default cleaned dataset:

`D:\MY DATA\PROGRAMMING\Auspify\TASK1\OUTPUT\netflix_cleaned.csv`

You can change the path in the dashboard sidebar.

## Run the web interface
Open a terminal in this task folder and run:

```bash
python -m streamlit run main.py
```

The dashboard opens in your browser. Use **Generate output files** / **Generate full report** to write analysis files.

## Output location
All generated files are saved inside this task's `OUTPUT` folder. No output is written outside this task folder.

## Notes
- The application uses an object-oriented analyzer class.
- Charts are interactive Plotly visualizations.
- CSV downloads are available in the dashboard.
- Release year means the title's listed release year, not the date Netflix added it.
