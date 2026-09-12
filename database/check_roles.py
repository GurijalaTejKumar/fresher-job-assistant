import sqlite3

DATABASE = "database/jobs.db"

connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()

query = """
SELECT
    id,
    company,
    job_title,
    experience_requirement
FROM jobs
WHERE degree = 'B.Tech'
  AND branch = 'Computer Science'
  AND graduation_year = 2026
  AND experience_requirement IN (
      'Fresher',
      '0-1 Years',
      '0-2 Years'
  )
  AND (
      LOWER(job_title) LIKE '%software%'
      OR LOWER(job_title) LIKE '%developer%'
      OR LOWER(job_title) LIKE '%programmer%'
  )
LIMIT 30
"""

rows = cursor.execute(query).fetchall()

print(f"Found {len(rows)} matching software/developer jobs:")
print()

for row in rows:
    print(row)

connection.close()