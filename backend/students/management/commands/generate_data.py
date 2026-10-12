"""
Generates a realistic-ish set of CSV exports, one per campus system.

We didn't have access to real college data, so this fakes it. Each file is
deliberately a bit messy in the way real exports are: roll numbers written
differently in every system, a few CGPAs typed on a percentage scale, "NA"
in score columns, duplicate feedback rows, LMS rows for students who left, etc.
The integration step has to deal with all of that.

It also writes alumni_outcomes.csv: last batch's indicators plus what actually
happened to them (academic trouble / not placed). The risk models learn from it.
"""
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

FIRST_NAMES = [
    "Aarav", "Aditi", "Akhil", "Ananya", "Arjun", "Bhavana", "Charan", "Deepika", "Divya", "Harsha",
    "Ishaan", "Kavya", "Keerthi", "Krishna", "Lakshmi", "Manoj", "Meghana", "Nikhil", "Nithya", "Pavan",
    "Pooja", "Pranav", "Priya", "Rahul", "Rakesh", "Ramya", "Rohit", "Sahithi", "Sai", "Sandeep",
    "Shreya", "Siddharth", "Sneha", "Srikanth", "Swathi", "Tarun", "Teja", "Varun", "Vamsi", "Yamini",
    "Abhinav", "Bhargavi", "Chaitanya", "Gayathri", "Hemanth", "Jahnavi", "Karthik", "Mounika", "Naveen", "Rupesh",
]
LAST_NAMES = [
    "Reddy", "Rao", "Sharma", "Naidu", "Kumar", "Varma", "Iyer", "Gupta", "Chowdary", "Patel",
    "Menon", "Pillai", "Galaji", "Yadav", "Shetty", "Joshi", "Nair", "Kulkarni", "Mishra", "Das",
]

SUBJECTS = {
    "CSE": ["Data Structures", "DBMS", "Operating Systems", "Computer Networks", "Software Engineering"],
    "ECE": ["Signals and Systems", "Analog Circuits", "Digital Electronics", "Microprocessors", "EM Waves"],
    "EEE": ["Power Systems", "Electrical Machines", "Control Systems", "Power Electronics", "Measurements"],
    "MECH": ["Thermodynamics", "Fluid Mechanics", "Machine Design", "Manufacturing", "Kinematics"],
}
DEPT_SIZE = {"CSE": 0.4, "ECE": 0.25, "EEE": 0.15, "MECH": 0.2}

MONTHS = ["2026-07", "2026-08", "2026-09", "2026-10"]
WEEKS = 14
CLUBS = ["Coding Club", "Robotics Club", "Literary Club", "NSS", "Music Club", "Entrepreneurship Cell", "Sports"]
EVENTS = ["Tech Fest", "Guest Lecture", "Workshop", "Paper Presentation", "Quiz"]
HACKATHONS = ["Smart India Hackathon", "byteXL Hackathon", "Campus Hack 2026", "HackOverflow"]
CERTS = ["NPTEL", "AWS Cloud Practitioner", "Coursera ML", "Google Data Analytics", "Cisco CCNA"]
COMMENTS_GOOD = ["Classes are useful", "Labs are good", "Faculty are supportive", "Happy with the course", ""]
COMMENTS_BAD = ["Too much workload", "Hard to follow lectures", "Not sure about placements", "Need more practical sessions", "Feeling lost this semester"]


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def clip(x, lo, hi):
    return float(np.clip(x, lo, hi))


class Command(BaseCommand):
    help = "Generate synthetic campus CSV exports into data/raw/"

    def add_arguments(self, parser):
        parser.add_argument("--students", type=int, default=600)
        parser.add_argument("--alumni", type=int, default=1500)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, *args, **opts):
        self.rng = np.random.default_rng(opts["seed"])
        random.seed(opts["seed"])
        out = settings.RAW_DATA_DIR
        out.mkdir(parents=True, exist_ok=True)

        people = self._make_people(opts["students"])
        self._write_current(people, out)
        self._write_alumni(opts["alumni"], out)
        self.stdout.write(self.style.SUCCESS(f"Wrote CSVs for {len(people)} students to {out}"))

    # ------------------------------------------------------------------ people

    def _make_people(self, n):
        rng = self.rng
        people = []
        counters = {}
        depts = list(DEPT_SIZE)
        for _ in range(n):
            dept = rng.choice(depts, p=list(DEPT_SIZE.values()))
            year = int(rng.choice([2, 3, 4], p=[0.34, 0.33, 0.33]))
            join_yy = {2: 25, 3: 24, 4: 23}[year]
            key = (join_yy, dept)
            counters[key] = counters.get(key, 0) + 1
            people.append({
                "roll": f"{join_yy}{dept}{counters[key]:03d}",
                "name": f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}",
                "dept": dept,
                "year": year,
                # hidden traits that drive everything below
                "ability": rng.normal(),
                "drive": rng.normal(),
                "career": rng.normal(),
                "slump": rng.random() < 0.12,
            })
        return people

    def _indicators(self, p):
        """Core indicators for one person. Shared by current students and alumni."""
        rng = self.rng
        a, d, c = p["ability"], p["drive"], p["career"]
        year = p.get("year", 4)

        cgpa = clip(7.0 + 1.1 * a + 0.3 * d + rng.normal(0, 0.4), 4.2, 9.9)
        backlogs = int(min(5, rng.poisson(np.exp(-1.1 - 1.1 * a - 0.5 * d))))
        attendance = clip(80 + 7 * d + 3 * a + rng.normal(0, 5), 40, 99)
        logins = max(0.2, 3.5 + 1.2 * d + rng.normal(0, 0.8))
        completion = clip(100 * sigmoid(1.2 + 1.2 * d + 0.4 * a + rng.normal(0, 0.3)), 5, 100)

        attempt_p = sigmoid(1.6 + 1.0 * c) if year >= 3 else sigmoid(-0.8 + 0.8 * c)
        aptitude = clip(55 + 12 * a + 6 * c + rng.normal(0, 10), 5, 100) if rng.random() < attempt_p else None
        coding = clip(48 + 10 * a + 13 * c + rng.normal(0, 12), 0, 100) if rng.random() < attempt_p else None
        mock_p = sigmoid(0.3 + 1.3 * c) if year >= 3 else sigmoid(-1.5 + c)
        mock = clip(55 + 10 * c + 5 * d + rng.normal(0, 10), 10, 100) if rng.random() < mock_p else None

        technical = clip(55 + 10 * a + 8 * c + rng.normal(0, 10), 10, 100)
        soft = clip(60 + 8 * c + 5 * d + rng.normal(0, 10), 10, 100)
        n_clubs = int(min(3, rng.poisson(np.exp(-0.4 + 0.5 * d))))
        n_events = int(min(8, rng.poisson(np.exp(0.5 + 0.5 * d + 0.2 * c))))
        n_hack = int(min(4, rng.poisson(np.exp(-1.2 + 0.4 * a + 0.7 * c))))
        n_cert = int(min(5, rng.poisson(np.exp(-0.5 + 0.3 * d + 0.6 * c))))

        return dict(cgpa=cgpa, backlogs=backlogs, attendance=attendance, logins=logins,
                    completion=completion, aptitude=aptitude, coding=coding, mock=mock,
                    technical=technical, soft=soft, clubs=n_clubs, events=n_events,
                    hackathons=n_hack, certifications=n_cert)

    # ---------------------------------------------------------- current batch

    def _write_current(self, people, out):
        rng = self.rng
        academics, marks, attendance, lms, engagement = [], [], [], [], []
        placement, skills, feedback = [], [], []

        for p in people:
            ind = self._indicators(p)
            p["ind"] = ind
            roll = p["roll"]

            # Exam cell export: clean-ish roll numbers, occasional bad CGPA
            cgpa_val = round(ind["cgpa"], 2)
            r = rng.random()
            if r < 0.02:
                cgpa_val = ""                       # missing
            elif r < 0.035:
                cgpa_val = round(ind["cgpa"] * 10, 1)  # someone typed a percentage
            academics.append({"Roll No": roll, "Student Name": p["name"], "Dept": p["dept"],
                              "Year": p["year"], "CGPA": cgpa_val, "Active Backlogs": ind["backlogs"]})

            for subj in SUBJECTS[p["dept"]]:
                m = clip(ind["cgpa"] * 9 + rng.normal(0, 8), 12, 100)
                marks.append({"RollNo": roll, "Subject": subj,
                              "Total Marks": "" if rng.random() < 0.01 else round(m)})

            # Attendance system lowercases everything and pads with spaces
            for mi, month in enumerate(MONTHS):
                base = ind["attendance"] - (5.5 * mi if p["slump"] else 0)
                for subj in SUBJECTS[p["dept"]]:
                    held = int(rng.integers(14, 20)) if month != "2026-10" else int(rng.integers(5, 9))
                    pct = clip(base + rng.normal(0, 6), 0, 100) / 100
                    attended = int(round(held * pct))
                    if rng.random() < 0.003:
                        attended = held + 2          # data entry slip
                    attendance.append({"student_roll": f" {roll.lower()} ", "subject": subj,
                                       "month": month, "classes_held": held, "classes_attended": attended})

            # LMS uses hyphenated ids
            lms_id = f"{roll[:2]}-{p['dept']}-{roll[-3:]}"
            for w in range(1, WEEKS + 1):
                fade = 0.55 if (p["slump"] and w > 8) else 1.0
                due = 2 if w % 2 == 0 else 1
                done = int(rng.binomial(due, min(1, ind["completion"] / 100 * fade)))
                lms.append({"user_id": lms_id, "week": w,
                            "logins": int(rng.poisson(ind["logins"] * fade)),
                            "assignments_due": due, "assignments_submitted": done})

            # Clubs / events office keeps a free-text-ish log
            start = date(2026, 1, 5)
            def add(kind, title):
                engagement.append({"roll_number": roll,
                                   "activity_type": random.choice([kind, kind.upper(), kind.lower() + " "]),
                                   "title": title,
                                   "date": (start + timedelta(days=int(rng.integers(0, 270)))).isoformat()})
            for club in random.sample(CLUBS, ind["clubs"]):
                add("Club", club)
            for _ in range(ind["events"]):
                add("Event", random.choice(EVENTS))
            for _ in range(ind["hackathons"]):
                add("Hackathon", random.choice(HACKATHONS))
            for cert in random.sample(CERTS, ind["certifications"]):
                add("Certification", cert)

            # Placement cell: spaces around ids and "NA" when not attempted
            if not (p["year"] == 2 and ind["aptitude"] is None and ind["mock"] is None and rng.random() < 0.6):
                fmt = lambda v: "NA" if v is None else round(v)
                placement.append({" Roll ": f" {roll} ", "aptitude_score": fmt(ind["aptitude"]),
                                  "coding_score": fmt(ind["coding"]), "mock_interview": fmt(ind["mock"])})

            # Skills team identifies people by college email
            if rng.random() > 0.02:
                skills.append({"email": f"{roll.lower()}@college.edu.in",
                               "technical_score": round(ind["technical"]),
                               "soft_skill_score": f"{round(ind['soft'])}%"})

            # Mid-semester feedback form
            mood = p["drive"] + (-1.2 if p["slump"] else 0)
            sat = int(round(clip(3.4 + 0.6 * mood + rng.normal(0, 0.7), 1, 5)))
            fac = int(round(clip(3.3 + 0.5 * p["drive"] + 0.4 * p["ability"] + rng.normal(0, 0.6), 1, 5)))
            row = {"Roll": roll, "satisfaction_1to5": sat, "faculty_rating_1to5": fac,
                   "comment": random.choice(COMMENTS_BAD if sat <= 2 else COMMENTS_GOOD)}
            if rng.random() > 0.03:
                feedback.append(row)
                if rng.random() < 0.04:
                    feedback.append(dict(row))   # form submitted twice

        # a handful of LMS accounts that don't belong to any current student
        for k in range(6):
            lms.append({"user_id": f"22-CSE-{900 + k}", "week": 1, "logins": 3,
                        "assignments_due": 1, "assignments_submitted": 1})

        frames = {
            "academics.csv": academics, "subject_marks.csv": marks, "attendance.csv": attendance,
            "lms_activity.csv": lms, "engagement.csv": engagement, "placement.csv": placement,
            "skills.csv": skills, "feedback.csv": feedback,
        }
        for name, rows in frames.items():
            pd.DataFrame(rows).to_csv(out / name, index=False)

    # ------------------------------------------------------------------ alumni

    def _write_alumni(self, n, out):
        rng = self.rng
        rows = []
        for i in range(n):
            p = {"ability": rng.normal(), "drive": rng.normal(), "career": rng.normal(), "year": 4}
            ind = self._indicators(p)
            a, d, c = p["ability"], p["drive"], p["career"]
            trouble = rng.random() < sigmoid(-1.8 - 1.5 * a - 1.1 * d)
            not_placed = rng.random() < sigmoid(-1.1 - 0.9 * a - 1.4 * c - 0.3 * d)
            rows.append({
                "alumni_id": f"A{i:05d}",
                "cgpa": round(ind["cgpa"], 2), "backlogs": ind["backlogs"],
                "attendance_pct": round(ind["attendance"], 1), "logins_per_week": round(ind["logins"], 2),
                "assignment_completion": round(ind["completion"], 1),
                "aptitude": round(ind["aptitude"] or 0), "coding": round(ind["coding"] or 0),
                "mock_interview": round(ind["mock"] or 0),
                "technical_skill": round(ind["technical"]), "soft_skill": round(ind["soft"]),
                "certifications": ind["certifications"], "hackathons": ind["hackathons"],
                "academic_trouble": int(trouble), "not_placed": int(not_placed),
            })
        pd.DataFrame(rows).to_csv(out / "alumni_outcomes.csv", index=False)
