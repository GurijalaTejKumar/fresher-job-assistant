import csv
import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).parent
CSV_FILE = DATABASE_DIR / "job_postings.csv"
DB_FILE = DATABASE_DIR / "jobs.db"


def create_database():
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT,
            job_title TEXT,
            location TEXT,
            graduation_year INTEGER,
            degree TEXT,
            branch TEXT,
            experience_requirement TEXT,
            skills TEXT,
            job_description TEXT
        )
    """)

    connection.commit()
    return connection


def import_jobs(connection):
    cursor = connection.cursor()

    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        rows = []

        for row in reader:
            rows.append((
                row["Company"],
                row["Job title"],
                row["Location"],
                row["Graduation year"],
                row["Degree"],
                row["Branch"],
                row["Experience requirement"],
                row["Skills"],
                row["Job description"],
            ))

    cursor.executemany("""
        INSERT INTO jobs (
            company,
            job_title,
            location,
            graduation_year,
            degree,
            branch,
            experience_requirement,
            skills,
            job_description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, rows)

    connection.commit()

    print(f"Imported {len(rows)} jobs into the database.")


def main():
    connection = create_database()

    try:
        import_jobs(connection)
    finally:
        connection.close()


if __name__ == "__main__":
    main()