"""Glues everything together: integrate -> score -> risk -> segment -> save."""
from pathlib import Path

import numpy as np
import pandas as pd
from django.conf import settings
from django.db import transaction

from ..models import PipelineRun, Student, SubjectPerformance
from .ingest import integrate
from .insights import attendance_drop, build_flags, cohort_insights, overall_risk, recommendations
from .risk import ACADEMIC_FEATURES, PLACEMENT_FEATURES, RiskModel, level
from .scoring import COMPONENTS, component_scores, success_scores
from .segments import assign_segment


def _clean(v):
    """numpy/pandas values -> plain python for the ORM and JSON fields."""
    if v is None:
        return None
    if isinstance(v, (float, np.floating)) and np.isnan(v):
        return None
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        return float(v)
    return v


def run(raw_dir=None):
    raw_dir = Path(raw_dir or settings.RAW_DATA_DIR)
    data = integrate(raw_dir)
    df = data["students"].copy()

    comps = component_scores(df)
    df["success_score"], df["baseline_score"], contribs, year_means = success_scores(df, comps)

    alumni = pd.read_csv(raw_dir / "alumni_outcomes.csv")
    academic_model = RiskModel("Academic risk", ACADEMIC_FEATURES, "academic_trouble").fit(alumni)
    placement_model = RiskModel("Placement risk", PLACEMENT_FEATURES, "not_placed").fit(alumni)

    df["academic_risk"], acad_contrib = academic_model.predict(df)
    p_prob, plac_contrib = placement_model.predict(df)
    # placement prediction only makes sense once placement prep has started
    df["placement_risk"] = np.where(df["year"] >= 3, p_prob, np.nan)
    df["academic_level"] = df["academic_risk"].map(level)
    df["placement_level"] = df["placement_risk"].map(level)
    df["attendance_drop"] = df["roll_no"].map(lambda r: attendance_drop(data["attendance_trend"].get(r, [])))
    for c in COMPONENTS:
        df[f"c_{c}"] = comps[c]

    records = []
    for i, row in df.iterrows():
        s = {k: _clean(v) for k, v in row.items()}
        contrib = {c: float(contribs.at[i, c]) for c in COMPONENTS}
        flags = build_flags(s)
        s["risk_level"] = overall_risk(s, flags)
        s["segment"] = assign_segment(s)
        s["flags"] = flags
        s["recommendations"] = recommendations(s, contrib)
        s["components"] = {c: float(comps.at[i, c]) for c in COMPONENTS}
        s["contributions"] = contrib
        s["academic_factors"] = academic_model.top_factors(acad_contrib[i])
        s["placement_factors"] = placement_model.top_factors(plac_contrib[i]) if s["year"] >= 3 else []
        records.append(s)

    scored = pd.DataFrame(records)
    summary = {
        "models": [academic_model.describe(), placement_model.describe()],
        "insights": cohort_insights(scored, data["attendance_trend"]),
        "year_component_means": year_means,
        "alumni_rows": len(alumni),
    }

    model_fields = {f.name for f in Student._meta.get_fields() if f.concrete} - {"id"}
    with transaction.atomic():
        Student.objects.all().delete()
        objs = []
        for s in records:
            obj = Student(**{k: v for k, v in s.items() if k in model_fields})
            obj.attendance_trend = data["attendance_trend"].get(s["roll_no"], [])
            obj.lms_trend = data["lms_trend"].get(s["roll_no"], [])
            objs.append(obj)
        Student.objects.bulk_create(objs, batch_size=500)

        ids = dict(Student.objects.values_list("roll_no", "id"))
        subj = data["subjects"]
        SubjectPerformance.objects.bulk_create([
            SubjectPerformance(student_id=ids[r.roll_no], subject=r.subject,
                               marks=_clean(r.marks), attendance_pct=_clean(r.attendance_pct))
            for r in subj.itertuples() if r.roll_no in ids
        ], batch_size=1000)

        run = PipelineRun.objects.create(report={"sources": data["report"]}, summary=summary)
    return run
