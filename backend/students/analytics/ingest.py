"""
Pulls the separate CSV exports together into one unified view per student.

Every system names students differently (23CSE014, " 23cse014 ", 23-CSE-014,
23cse014@college.edu.in), so the first job is always to normalise the id.
Everything we fix or drop gets written to a SourceLog so the "Data sources"
page can show exactly what happened to each file.
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

ID_PATTERN = re.compile(r"(\d{2})\s*-?\s*([A-Za-z]{2,5})\s*-?\s*(\d{3})")

SOURCE_FILES = {
    "academics": ("academics.csv", "Exam cell"),
    "marks": ("subject_marks.csv", "Exam cell (subject marks)"),
    "attendance": ("attendance.csv", "Attendance system"),
    "lms": ("lms_activity.csv", "LMS"),
    "engagement": ("engagement.csv", "Clubs & events office"),
    "placement": ("placement.csv", "Placement cell"),
    "skills": ("skills.csv", "Skills assessment team"),
    "feedback": ("feedback.csv", "Feedback forms"),
}


def normalize_id(raw):
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return None
    m = ID_PATTERN.search(str(raw))
    if not m:
        return None
    yy, dept, num = m.groups()
    return f"{yy}{dept.upper()}{num}"


class SourceLog:
    def __init__(self, key):
        self.key = key
        self.file, self.system = SOURCE_FILES[key]
        self.rows_in = 0
        self.rows_used = 0
        self.unmatched = set()
        self.fixes = []

    def fix(self, what, count):
        count = int(count)
        if count:
            self.fixes.append({"issue": what, "rows": count})

    def as_dict(self):
        return {
            "key": self.key, "file": self.file, "system": self.system,
            "rows_in": int(self.rows_in), "rows_used": int(self.rows_used),
            "unmatched_ids": sorted(self.unmatched)[:20], "unmatched_count": len(self.unmatched),
            "fixes": self.fixes,
        }


def _read(raw_dir, key, log):
    path = Path(raw_dir) / SOURCE_FILES[key][0]
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    log.rows_in = len(df)
    return df


def _num(series):
    """Turn '72%', 'NA', '' and friends into floats/NaN."""
    cleaned = series.astype(str).str.replace("%", "", regex=False).str.strip()
    cleaned = cleaned.replace({"NA": np.nan, "N/A": np.nan, "na": np.nan, "-": np.nan, "": np.nan})
    return pd.to_numeric(cleaned, errors="coerce")


def _attach_ids(df, id_col, roster, log):
    df = df.copy()
    df["roll_no"] = df[id_col].map(normalize_id)
    bad = df["roll_no"].isna()
    log.fix("Unreadable student id, row dropped", bad.sum())
    df = df[~bad]
    stray = ~df["roll_no"].isin(roster)
    log.unmatched.update(df.loc[stray, "roll_no"].unique())
    log.fix("Id not on the exam cell roster, row dropped", stray.sum())
    return df[~stray]


def integrate(raw_dir):
    logs = {k: SourceLog(k) for k in SOURCE_FILES}

    # --- academics is the master roster -----------------------------------
    lg = logs["academics"]
    ac = _read(raw_dir, "academics", lg)
    ac["roll_no"] = ac["Roll No"].map(normalize_id)
    lg.fix("Unreadable roll number, row dropped", ac["roll_no"].isna().sum())
    ac = ac.dropna(subset=["roll_no"])
    lg.fix("Duplicate roll number, kept latest", ac.duplicated("roll_no").sum())
    ac = ac.drop_duplicates("roll_no", keep="last")

    ac["cgpa"] = _num(ac["CGPA"])
    on_pct_scale = ac["cgpa"] > 10
    lg.fix("CGPA entered as a percentage, divided by 10", on_pct_scale.sum())
    ac.loc[on_pct_scale, "cgpa"] = ac.loc[on_pct_scale, "cgpa"] / 10
    ac["backlogs"] = _num(ac["Active Backlogs"]).fillna(0).astype(int)
    students = pd.DataFrame({
        "roll_no": ac["roll_no"],
        "name": ac["Student Name"].str.strip().str.title(),
        "department": ac["Dept"].str.strip().str.upper(),
        "year": _num(ac["Year"]).astype(int),
        "cgpa": ac["cgpa"],
        "backlogs": ac["backlogs"],
    }).set_index("roll_no")
    roster = set(students.index)

    # --- subject marks ------------------------------------------------------
    lg = logs["marks"]
    mk = _attach_ids(_read(raw_dir, "marks", lg), "RollNo", roster, lg)
    mk["marks"] = _num(mk["Total Marks"]).clip(0, 100)
    lg.fix("Blank marks, left empty", mk["marks"].isna().sum())
    mk = mk.rename(columns={"Subject": "subject"})[["roll_no", "subject", "marks"]]
    lg.rows_used = len(mk)

    # CGPA gaps: estimate from the student's own subject marks rather than a flat average
    missing_cgpa = students["cgpa"].isna()
    if missing_cgpa.any():
        est = (mk.groupby("roll_no")["marks"].mean() / 9).clip(4, 10)
        students.loc[missing_cgpa, "cgpa"] = est.reindex(students.index[missing_cgpa]).values
        still = students["cgpa"].isna()
        students.loc[still, "cgpa"] = students.groupby("department")["cgpa"].transform("median")[still]
        logs["academics"].fix("Missing CGPA, estimated from subject marks", missing_cgpa.sum())
    students["cgpa"] = students["cgpa"].round(2)
    logs["academics"].rows_used = len(students)

    # --- attendance -----------------------------------------------------------
    lg = logs["attendance"]
    at = _attach_ids(_read(raw_dir, "attendance", lg), "student_roll", roster, lg)
    at["held"] = _num(at["classes_held"]).fillna(0)
    at["attended"] = _num(at["classes_attended"]).fillna(0)
    over = at["attended"] > at["held"]
    lg.fix("Attended more classes than were held, capped", over.sum())
    at.loc[over, "attended"] = at.loc[over, "held"]
    lg.rows_used = len(at)

    totals = at.groupby("roll_no")[["held", "attended"]].sum()
    students["attendance_pct"] = (totals["attended"] / totals["held"] * 100).round(1)
    by_subject = at.groupby(["roll_no", "subject"])[["held", "attended"]].sum()
    by_subject["attendance_pct"] = (by_subject["attended"] / by_subject["held"] * 100).round(1)
    monthly = at.groupby(["roll_no", "month"])[["held", "attended"]].sum()
    monthly["pct"] = (monthly["attended"] / monthly["held"] * 100).round(1)
    attendance_trend = {
        roll: [{"period": m, "value": float(v)} for (_, m), v in grp["pct"].items()]
        for roll, grp in monthly.groupby(level=0)
    }

    subjects = mk.merge(by_subject["attendance_pct"].reset_index(), on=["roll_no", "subject"], how="outer")

    # --- LMS --------------------------------------------------------------------
    lg = logs["lms"]
    lm = _attach_ids(_read(raw_dir, "lms", lg), "user_id", roster, lg)
    for col in ["week", "logins", "assignments_due", "assignments_submitted"]:
        lm[col] = _num(lm[col]).fillna(0)
    over = lm["assignments_submitted"] > lm["assignments_due"]
    lg.fix("More submissions than assignments due, capped", over.sum())
    lm.loc[over, "assignments_submitted"] = lm.loc[over, "assignments_due"]
    lg.rows_used = len(lm)

    agg = lm.groupby("roll_no").agg(logins=("logins", "mean"), due=("assignments_due", "sum"),
                                    done=("assignments_submitted", "sum"))
    students["logins_per_week"] = agg["logins"].round(2)
    students["assignment_completion"] = (agg["done"] / agg["due"].replace(0, np.nan) * 100).round(1)
    lms_trend = {
        roll: [{"period": f"W{int(w)}", "value": float(v)} for w, v in zip(grp["week"], grp["logins"])]
        for roll, grp in lm.sort_values("week").groupby("roll_no")
    }

    # --- engagement ---------------------------------------------------------------
    lg = logs["engagement"]
    en = _attach_ids(_read(raw_dir, "engagement", lg), "roll_number", roster, lg)
    raw_type = en["activity_type"]
    en["kind"] = raw_type.str.strip().str.lower()
    lg.fix("Inconsistent activity type casing/spacing, normalised", (raw_type != raw_type.str.strip().str.title()).sum())
    lg.fix("Same club listed twice for a student, counted once", en[en["kind"] == "club"].duplicated(["roll_no", "title"]).sum())
    lg.rows_used = len(en)
    clubs = en[en["kind"] == "club"].drop_duplicates(["roll_no", "title"]).groupby("roll_no").size()
    counts = en[en["kind"] != "club"].groupby(["roll_no", "kind"]).size().unstack(fill_value=0)
    students["clubs"] = clubs
    for kind, col in [("event", "events"), ("hackathon", "hackathons"), ("certification", "certifications")]:
        students[col] = counts[kind] if kind in counts else 0

    # --- placement ------------------------------------------------------------------
    lg = logs["placement"]
    pl = _attach_ids(_read(raw_dir, "placement", lg), "Roll", roster, lg)
    pl = pl.drop_duplicates("roll_no", keep="last").set_index("roll_no")
    for src, col in [("aptitude_score", "aptitude"), ("coding_score", "coding"), ("mock_interview", "mock_interview")]:
        vals = _num(pl[src]).clip(0, 100)
        lg.fix(f"'{src}' not attempted (NA)", vals.isna().sum())
        students[col] = vals
    lg.fix("Student missing from placement file, treated as not attempted", len(roster - set(pl.index)))
    lg.rows_used = len(pl)

    # --- skills ------------------------------------------------------------------------
    lg = logs["skills"]
    sk = _read(raw_dir, "skills", lg)
    lg.fix("Matched by college email instead of roll number", len(sk))
    sk = _attach_ids(sk, "email", roster, lg).drop_duplicates("roll_no", keep="last").set_index("roll_no")
    lg.fix("Soft skill score stored as text like '72%', converted", sk["soft_skill_score"].str.contains("%").sum())
    students["technical_skill"] = _num(sk["technical_score"]).clip(0, 100)
    students["soft_skill"] = _num(sk["soft_skill_score"]).clip(0, 100)
    lg.rows_used = len(sk)
    no_skills = students["technical_skill"].isna()
    lg.fix("No skills assessment on record, filled with year median", no_skills.sum())
    for col in ["technical_skill", "soft_skill"]:
        students[col] = students[col].fillna(students.groupby("year")[col].transform("median"))

    # --- feedback ------------------------------------------------------------------------
    lg = logs["feedback"]
    fb = _attach_ids(_read(raw_dir, "feedback", lg), "Roll", roster, lg)
    lg.fix("Form submitted more than once, kept one", fb.duplicated().sum())
    fb = fb.drop_duplicates().drop_duplicates("roll_no", keep="last").set_index("roll_no")
    lg.rows_used = len(fb)
    students["satisfaction"] = _num(fb["satisfaction_1to5"]).clip(1, 5)
    students["faculty_rating"] = _num(fb["faculty_rating_1to5"]).clip(1, 5)
    no_fb = students["satisfaction"].isna()
    lg.fix("No feedback submitted, assumed neutral (3/5)", no_fb.sum())
    students[["satisfaction", "faculty_rating"]] = students[["satisfaction", "faculty_rating"]].fillna(3)

    # anything still empty after all that (e.g. a student with zero LMS rows)
    for col in ["clubs", "events", "hackathons", "certifications"]:
        students[col] = students[col].fillna(0).astype(int)
    for col in ["attendance_pct", "logins_per_week", "assignment_completion"]:
        students[col] = students[col].fillna(0)

    return {
        "students": students.reset_index(),
        "subjects": subjects,
        "attendance_trend": attendance_trend,
        "lms_trend": lms_trend,
        "report": [logs[k].as_dict() for k in SOURCE_FILES],
    }
