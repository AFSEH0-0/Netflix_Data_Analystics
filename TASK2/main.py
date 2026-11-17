from pathlib import Path
from content_analyzer import NetflixContentAnalyzer
from dashboard import NetflixDashboard


def main():
    project_dir = Path(__file__).resolve().parent
    default_csv = project_dir.parent / "TASK1" / "OUTPUT" / "netflix_cleaned.csv"

    analyzer = NetflixContentAnalyzer(default_csv)
    dashboard = NetflixDashboard(analyzer)
    dashboard.run()


if __name__ == "__main__":
    main()
