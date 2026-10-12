"""
Student Success Score.

Seven component scores, each on a 0-100 scale, combined with a weighted sum.
The weights shift for 2nd years because it isn't fair to judge someone on
placement readiness a year before placement prep even starts.

Explainability falls straight out of the maths: since the score is linear,

    score - year_average = sum( weight_i * (component_i - year_average_i) )

so every point a student is above or below their year's average can be pinned
on a specific component. That's what the "why this score" chart shows.
"""
import pandas as pd

COMPONENTS = ["academic", "attendance", "lms", "placement", "skills", "engagement", "feedback"]

COMPONENT_LABELS = {
    "academic": "Academics",
    "attendance": "Attendance",
    "lms": "LMS activity",
    "placement": "Placement readiness",
    "skills": "Skills",
    "engagement": "Engagement",
    "feedback": "Feedback",
}

WEIGHTS = {
    "default": {"academic": 0.25, "attendance": 0.15, "lms": 0.15, "placement": 0.20,
                "skills": 0.10, "engagement": 0.10, "feedback": 0.05},
    2: {"academic": 0.30, "attendance": 0.20, "lms": 0.15, "placement": 0.05,
        "skills": 0.10, "engagement": 0.15, "feedback": 0.05},
}


def weights_for(year):
    return WEIGHTS.get(int(year), WEIGHTS["default"])


def component_scores(df):
    c = pd.DataFrame(index=df.index)
    # CGPA carries most of it, each active backlog knocks the rest down
    c["academic"] = 0.75 * df["cgpa"] * 10 + 0.25 * (100 - df["backlogs"].clip(upper=4) * 25)
    c["attendance"] = df["attendance_pct"].clip(0, 100)
    # 5 logins a week is treated as "fully active"; submitting work matters more than logging in
    c["lms"] = 0.35 * (df["logins_per_week"] / 5 * 100).clip(upper=100) + 0.65 * df["assignment_completion"]
    # a missing placement test counts as 0: no evidence of readiness yet
    c["placement"] = df[["aptitude", "coding", "mock_interview"]].fillna(0).mean(axis=1)
    c["skills"] = 0.6 * df["technical_skill"] + 0.4 * df["soft_skill"]
    c["engagement"] = (df["clubs"] * 12 + df["events"] * 6 + df["hackathons"] * 15
                       + df["certifications"] * 12).clip(upper=100)
    c["feedback"] = ((df["satisfaction"] - 1) / 4 * 50) + ((df["faculty_rating"] - 1) / 4 * 50)
    return c[COMPONENTS].clip(0, 100).round(1)


def success_scores(df, comps):
    """Returns score, year baseline and per-component contributions for every student."""
    score = pd.Series(index=df.index, dtype=float)
    baseline = pd.Series(index=df.index, dtype=float)
    contribs = pd.DataFrame(index=df.index, columns=COMPONENTS, dtype=float)
    year_means = {}

    for year, idx in df.groupby("year").groups.items():
        w = pd.Series(weights_for(year))[COMPONENTS]
        block = comps.loc[idx]
        means = block.mean()
        score.loc[idx] = (block * w).sum(axis=1)
        baseline.loc[idx] = float((means * w).sum())
        contribs.loc[idx] = (block - means) * w
        year_means[int(year)] = means.round(1).to_dict()

    return score.round(1), baseline.round(1), contribs.round(2), year_means
