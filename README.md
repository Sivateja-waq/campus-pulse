# Campus Pulse

Our submission for KPMG's Challenge 4: AI-Powered Student Analytics and Success Platform.

Campus Pulse takes the exports a college already has (exam cell, attendance, LMS,
clubs/events, placement cell, skills team, feedback forms), stitches them into one
record per student, gives every student a Student Success Score, predicts who is
likely to struggle academically or miss out on placements, and tells faculty what
to do about it.

Stack: Django + pandas + scikit-learn on the backend, React (Vite + Recharts) on the front.

## Running it

You need Python 3.10+ and Node 18+.

```bash
# backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py generate_data     # writes the sample CSVs to data/raw/ (already included, safe to rerun)
python manage.py run_pipeline      # integrates, scores and loads all students
python manage.py runserver
```

```bash
# frontend, in a second terminal
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to Django on port 8000.

## Project layout

```
backend/
  data/raw/                     one CSV per campus system + alumni_outcomes.csv
  students/
    analytics/
      ingest.py                 cleaning + merging the sources (the data integration part)
      scoring.py                Student Success Score and its explanation
      risk.py                   academic / placement risk models
      segments.py               named student segments and their playbooks
      insights.py               flags, recommended actions, cohort insights
      pipeline.py               runs all of the above and saves to the DB
    management/commands/        generate_data, run_pipeline
    views.py, urls.py           JSON API
frontend/src/
  pages/                        Overview, Students, StudentDetail, Segments, DataSources
```

## API

| Endpoint | What it returns |
|---|---|
| `GET /api/overview/` | KPIs, score distribution, risk by department, trends, insights, watchlist |
| `GET /api/students/?q=&department=&year=&risk=&segment=&sort=` | filtered student list |
| `GET /api/students/<roll_no>/` | everything about one student |
| `GET /api/segments/` | segments with counts and averages |
| `GET /api/data/` | integration report + model metrics |
| `POST /api/data/rerun/` | rerun the pipeline |
| `POST /api/data/upload/<source>/` | replace one source CSV and rerun |

## About the data

We didn't have real student data, so `generate_data` creates 600 students across
CSE, ECE, EEE and MECH (years 2 to 4) plus 1,500 alumni records with known outcomes.
Each file is messy on purpose, the way real exports are: roll numbers formatted
differently in every system (`23CSE014`, ` 23cse014 `, `23-CSE-014`,
`23cse014@college.edu.in`), CGPAs typed as percentages, `NA` in score columns,
`72%` stored as text, duplicate feedback submissions, LMS accounts for students who
aren't on the roll. Everything the pipeline fixes shows up on the Data sources page.

To use real data, drop CSVs with the same columns into `backend/data/raw/` (or
upload them from the Data sources page) and rerun the pipeline.

## Things we'd do next

- Login and role-based access (HOD sees the department, advisor sees their section)
- Track interventions and measure whether flagged students actually improved
- Retrain the risk models every semester as real outcomes come in
- Alerts to class advisors when a student crosses a threshold mid-week
