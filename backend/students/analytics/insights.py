"""Turns numbers into flags, next steps and plain-English cohort observations."""
import numpy as np
import pandas as pd

from .scoring import COMPONENT_LABELS

ACTIONS = {
    "academic": "Remedial sessions in weakest subjects; pair with a peer tutor.",
    "attendance": "Class advisor to talk to the student about attendance before it hits the detention line.",
    "lms": "Faculty to follow up on pending LMS assignments; set weekly submission reminders.",
    "placement": "Enrol in the next aptitude + coding bootcamp and book a mock interview.",
    "skills": "Recommend a short skill course (technical or communication, whichever is lower).",
    "engagement": "Encourage joining one club or a hackathon team this semester.",
    "feedback": "Counsellor check-in: feedback suggests the student isn't happy with how things are going.",
}


def attendance_drop(trend):
    if len(trend) < 3:
        return 0.0
    vals = [p["value"] for p in trend]
    return round(float(np.mean(vals[:2]) - np.mean(vals[-2:])), 1)


def build_flags(s):
    flags = []

    def add(sev, text):
        flags.append({"severity": sev, "text": text})

    if s["attendance_pct"] < 65:
        add("high", f"Attendance {s['attendance_pct']:.0f}%, below the 65% detention line")
    elif s["attendance_pct"] < 75:
        add("medium", f"Attendance {s['attendance_pct']:.0f}%, short of the 75% requirement")
    if s["attendance_drop"] >= 10:
        add("medium", f"Attendance down {s['attendance_drop']:.0f} points since July")
    if s["backlogs"] >= 3:
        add("high", f"{s['backlogs']} active backlogs")
    elif s["backlogs"] >= 1:
        add("medium", f"{s['backlogs']} active backlog{'s' if s['backlogs'] > 1 else ''}")
    if s["assignment_completion"] < 50:
        add("medium", f"Only {s['assignment_completion']:.0f}% of LMS assignments submitted")
    if s["academic_level"] == "High":
        add("high", f"Academic risk model: {s['academic_risk'] * 100:.0f}% chance of serious academic trouble")
    if s["placement_level"] == "High":
        add("high", f"Placement risk model: {s['placement_risk'] * 100:.0f}% chance of not being placed")
    if s["year"] >= 3:
        if s["mock_interview"] is None:
            add("medium", "No mock interview on record")
        if s["coding"] is None or s["coding"] < 40:
            add("medium", "Coding assessment missing or below 40")
    if s["satisfaction"] <= 2:
        add("medium", f"Rated the semester {s['satisfaction']:.0f}/5 in feedback")
    return flags


def overall_risk(s, flags):
    if any(f["severity"] == "high" for f in flags):
        return "High"
    medium = sum(f["severity"] == "medium" for f in flags)
    if "Medium" in (s["academic_level"], s["placement_level"]) or medium >= 2 or s["success_score"] < 50:
        return "Medium"
    return "Low"


def recommendations(s, contributions):
    recs = []
    # biggest drags on the score first
    for comp, value in sorted(contributions.items(), key=lambda kv: kv[1]):
        if value < -1.0 and len(recs) < 3:
            if comp == "placement" and s["year"] == 2:
                continue
            recs.append({"area": COMPONENT_LABELS[comp], "action": ACTIONS[comp]})
    if s["backlogs"] >= 1:
        recs.insert(0, {"area": "Backlogs", "action": f"Backlog clearance plan for {s['backlogs']} subject(s) before the next exam cycle."})
    if s["year"] >= 3 and s["mock_interview"] is None and not any(r["area"] == "Placement readiness" for r in recs):
        recs.append({"area": "Placement readiness", "action": "Book a mock interview; there's none on record."})
    if not recs:
        recs.append({"area": "Growth", "action": "On track. Offer stretch opportunities: peer mentoring, hackathons, research projects."})
    return recs[:5]


def cohort_insights(df, attendance_trends):
    """A handful of observations a HOD would actually care about. df is the scored frame."""
    out = []
    low_att = df[df["attendance_pct"] < 75]
    ok_att = df[df["attendance_pct"] >= 75]
    if len(low_att) and len(ok_att):
        a = (low_att["academic_level"] == "High").mean() * 100
        b = (ok_att["academic_level"] == "High").mean() * 100
        out.append(f"{a:.0f}% of students under 75% attendance are high academic risk, compared with {b:.0f}% of those above it. "
                   f"Attendance is the earliest warning sign we have.")

    months = {}
    for trend in attendance_trends.values():
        for p in trend:
            months.setdefault(p["period"], []).append(p["value"])
    if len(months) >= 2:
        keys = sorted(months)
        first, last = np.mean(months[keys[0]]), np.mean(months[keys[-1]])
        direction = "dropped" if last < first else "rose"
        name = lambda k: pd.Timestamp(k + "-01").strftime("%B")
        out.append(f"Average attendance {direction} from {first:.0f}% in {name(keys[0])} to {last:.0f}% in {name(keys[-1])}.")

    hidden = df[(df["year"] >= 3) & (df["cgpa"] >= 8) & (df["mock_interview"].isna())]
    if len(hidden):
        out.append(f"{len(hidden)} senior students have a CGPA of 8+ but have never sat a mock interview. "
                   f"They're the easiest placement wins on campus.")

    dept = df.groupby("department")["risk_level"].apply(lambda r: (r == "High").mean() * 100).sort_values()
    if len(dept) > 1:
        out.append(f"{dept.index[-1]} has the highest share of high-risk students ({dept.iloc[-1]:.0f}%); "
                   f"{dept.index[0]} has the lowest ({dept.iloc[0]:.0f}%).")

    lazy = df[df["assignment_completion"] < 60]["cgpa"].mean()
    diligent = df[df["assignment_completion"] >= 90]["cgpa"].mean()
    if not np.isnan(lazy) and not np.isnan(diligent):
        out.append(f"Students who submit 90%+ of LMS assignments average a {diligent:.2f} CGPA, versus {lazy:.2f} for those under 60%.")

    sliding = int((df["attendance_drop"] >= 10).sum())
    if sliding:
        out.append(f"{sliding} students' attendance has fallen 10+ points this semester. Most of them aren't failing yet, which is why they're worth catching now.")
    return out
