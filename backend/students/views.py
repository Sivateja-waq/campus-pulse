import json
from collections import Counter, defaultdict

from django.conf import settings
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .analytics import pipeline
from .analytics.ingest import SOURCE_FILES
from .analytics.scoring import COMPONENT_LABELS, weights_for
from .analytics.segments import SEGMENT_BY_KEY, public_segments
from .models import PipelineRun, Student

RISK_ORDER = {"High": 0, "Medium": 1, "Low": 2}

LIST_FIELDS = ["roll_no", "name", "department", "year", "cgpa", "attendance_pct",
               "success_score", "risk_level", "segment", "academic_risk", "placement_risk"]


def _latest_run():
    return PipelineRun.objects.first()


def _row(s):
    d = {f: getattr(s, f) for f in LIST_FIELDS}
    d["segment_name"] = SEGMENT_BY_KEY.get(s.segment, {}).get("name", s.segment)
    d["flag_count"] = len(s.flags)
    return d


@require_GET
def meta(request):
    return JsonResponse({
        "departments": sorted(Student.objects.values_list("department", flat=True).order_by().distinct()),
        "years": sorted(Student.objects.values_list("year", flat=True).order_by().distinct()),
        "segments": [{"key": s["key"], "name": s["name"]} for s in public_segments()],
        "components": COMPONENT_LABELS,
    })


@require_GET
def overview(request):
    qs = Student.objects.all()
    total = qs.count()
    if not total:
        return JsonResponse({"empty": True})

    risk = Counter(qs.values_list("risk_level", flat=True))
    scores = list(qs.values_list("success_score", flat=True))
    buckets = [{"range": f"{b}-{b + 9}", "count": 0} for b in range(0, 100, 10)]
    for sc in scores:
        buckets[min(int(sc // 10), 9)]["count"] += 1

    by_dept = defaultdict(lambda: {"High": 0, "Medium": 0, "Low": 0})
    for dept, lvl in qs.values_list("department", "risk_level"):
        by_dept[dept][lvl] += 1

    month_vals, week_vals = defaultdict(list), defaultdict(list)
    for att, lms in qs.values_list("attendance_trend", "lms_trend"):
        for p in att:
            month_vals[p["period"]].append(p["value"])
        for p in lms:
            week_vals[p["period"]].append(p["value"])
    avg = lambda xs: round(sum(xs) / len(xs), 1)

    seg_counts = Counter(qs.values_list("segment", flat=True))
    watchlist = qs.filter(risk_level="High").order_by("success_score")[:8]
    run = _latest_run()

    return JsonResponse({
        "kpis": {
            "students": total,
            "avg_score": round(sum(scores) / total, 1),
            "high": risk.get("High", 0),
            "medium": risk.get("Medium", 0),
            "low": risk.get("Low", 0),
            "avg_attendance": round(qs.aggregate(a=Avg("attendance_pct"))["a"], 1),
        },
        "score_distribution": buckets,
        "risk_by_department": [{"department": d, **v} for d, v in sorted(by_dept.items())],
        "attendance_trend": [{"period": k, "value": avg(v)} for k, v in sorted(month_vals.items())],
        "lms_trend": sorted(({"period": k, "value": avg(v)} for k, v in week_vals.items()),
                            key=lambda p: int(p["period"][1:])),
        "segments": [{"key": s["key"], "name": s["name"], "count": seg_counts.get(s["key"], 0)}
                     for s in public_segments()],
        "insights": run.summary.get("insights", []) if run else [],
        "watchlist": [_row(s) for s in watchlist],
        "updated_at": run.created_at.isoformat() if run else None,
    })


@require_GET
def student_list(request):
    qs = Student.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(roll_no__icontains=q))
    for param, field in [("department", "department"), ("year", "year"),
                         ("risk", "risk_level"), ("segment", "segment")]:
        val = request.GET.get(param)
        if val:
            qs = qs.filter(**{field: val})

    rows = [_row(s) for s in qs]
    sort = request.GET.get("sort", "risk")
    desc = sort.startswith("-")
    key = sort.lstrip("-")
    if key == "risk":
        rows.sort(key=lambda r: (RISK_ORDER[r["risk_level"]], r["success_score"]), reverse=desc)
    elif key in LIST_FIELDS:
        rows.sort(key=lambda r: (r[key] is None, r[key]), reverse=desc)
    return JsonResponse({"count": len(rows), "results": rows})


@require_GET
def student_detail(request, roll_no):
    s = get_object_or_404(Student, roll_no=roll_no.upper())
    run = _latest_run()
    year_means = (run.summary.get("year_component_means", {}) if run else {}).get(str(s.year), {})
    weights = weights_for(s.year)

    data = _row(s)
    data.update({
        "backlogs": s.backlogs,
        "indicators": {
            "CGPA": s.cgpa, "Active backlogs": s.backlogs, "Attendance %": s.attendance_pct,
            "LMS logins / week": s.logins_per_week, "Assignments submitted %": s.assignment_completion,
            "Clubs": s.clubs, "Events": s.events, "Hackathons": s.hackathons,
            "Certifications": s.certifications, "Aptitude": s.aptitude, "Coding": s.coding,
            "Mock interview": s.mock_interview, "Technical skills": s.technical_skill,
            "Soft skills": s.soft_skill, "Satisfaction (1-5)": s.satisfaction,
            "Faculty rating (1-5)": s.faculty_rating,
        },
        "components": [
            {"key": k, "label": COMPONENT_LABELS[k], "score": v, "year_avg": year_means.get(k),
             "weight": weights[k], "contribution": s.contributions.get(k, 0)}
            for k, v in s.components.items()
        ],
        "baseline_score": s.baseline_score,
        "academic_factors": s.academic_factors,
        "placement_factors": s.placement_factors,
        "flags": s.flags,
        "recommendations": s.recommendations,
        "segment_info": {k: v for k, v in SEGMENT_BY_KEY.get(s.segment, {}).items() if k != "rule"},
        "attendance_trend": s.attendance_trend,
        "lms_trend": s.lms_trend,
        "subjects": list(s.subjects.values("subject", "marks", "attendance_pct")),
    })
    return JsonResponse(data)


@require_GET
def segments(request):
    out = []
    for seg in public_segments():
        qs = Student.objects.filter(segment=seg["key"])
        stats = qs.aggregate(score=Avg("success_score"), cgpa=Avg("cgpa"), att=Avg("attendance_pct"))
        out.append({
            **seg,
            "count": qs.count(),
            "avg_score": round(stats["score"] or 0, 1),
            "avg_cgpa": round(stats["cgpa"] or 0, 2),
            "avg_attendance": round(stats["att"] or 0, 1),
            "high_risk": qs.filter(risk_level="High").count(),
            "by_year": dict(Counter(qs.values_list("year", flat=True))),
        })
    return JsonResponse({"segments": out})


@require_GET
def data_report(request):
    run = _latest_run()
    if not run:
        return JsonResponse({"empty": True})
    return JsonResponse({
        "updated_at": run.created_at.isoformat(),
        "sources": run.report.get("sources", []),
        "models": run.summary.get("models", []),
        "alumni_rows": run.summary.get("alumni_rows"),
        "students": Student.objects.count(),
    })


# Dev-friendly endpoints for refreshing data from the UI. No auth on purpose
# for the demo, these need a login before this goes near real student data.
@csrf_exempt
@require_POST
def rerun(request):
    pipeline.run()
    return JsonResponse({"ok": True, "students": Student.objects.count()})


@csrf_exempt
@require_POST
def upload_source(request, source):
    if source not in SOURCE_FILES:
        return JsonResponse({"error": f"Unknown source '{source}'"}, status=400)
    upload = request.FILES.get("file")
    if not upload or not upload.name.lower().endswith(".csv"):
        return JsonResponse({"error": "Attach a .csv file"}, status=400)

    target = settings.RAW_DATA_DIR / SOURCE_FILES[source][0]
    backup = target.read_bytes() if target.exists() else None
    target.write_bytes(upload.read())
    try:
        pipeline.run()
    except Exception as exc:  # bad file: put the old one back so the dashboard keeps working
        if backup is not None:
            target.write_bytes(backup)
        return JsonResponse({"error": f"Couldn't process that file: {exc}"}, status=400)
    return JsonResponse({"ok": True, "students": Student.objects.count()})
