"""
Named student segments. Rule-based on purpose: a clustering algorithm will
happily give you "cluster 3", but a placement officer needs "strong in class,
not ready for interviews" and a clear next step. Order matters, first match wins.
"""

SEGMENTS = [
    {
        "key": "critical",
        "name": "Needs immediate support",
        "description": "High academic risk and attendance below 65%.",
        "action": "Assign a faculty mentor this week and loop in parents/HOD for detention-zone attendance.",
        "rule": lambda s: s["academic_level"] == "High" and s["attendance_pct"] < 65,
    },
    {
        "key": "declining",
        "name": "Sliding this semester",
        "description": "Attendance has dropped 10+ points since the start of the semester.",
        "action": "Early check-in by the class advisor before it shows up in marks.",
        "rule": lambda s: s["attendance_drop"] >= 10,
    },
    {
        "key": "scholar_not_ready",
        "name": "Strong academics, low placement readiness",
        "description": "Academic score 78+ (roughly CGPA 7.7, no backlogs) but placement readiness under 45.",
        "action": "Push into aptitude + mock interview drives; these students convert well with a little prep.",
        "rule": lambda s: s["year"] >= 3 and s["c_academic"] >= 78 and s["c_placement"] < 45,
    },
    {
        "key": "job_ready_slipping",
        "name": "Placement-ready, academics slipping",
        "description": "Good placement scores but carrying backlogs or a weak academic score.",
        "action": "Backlog clearance plan so eligibility criteria don't cost them offers.",
        "rule": lambda s: s["c_placement"] >= 60 and (s["backlogs"] >= 1 or s["c_academic"] < 60),
    },
    {
        "key": "disengaged",
        "name": "Quietly disengaged",
        "description": "Low LMS activity and almost no clubs, events or certifications.",
        "action": "Nudge into one club or short certification; low engagement usually precedes low attendance.",
        "rule": lambda s: s["c_lms"] < 50 and s["c_engagement"] < 25,
    },
    {
        "key": "all_rounder",
        "name": "All-rounders",
        "description": "Success score 72+ with no risk flags.",
        "action": "Peer mentors, hackathon teams, and stretch opportunities.",
        "rule": lambda s: s["success_score"] >= 72 and s["risk_level"] == "Low",
    },
    {
        "key": "steady",
        "name": "Steady middle",
        "description": "No major concerns, no standout strengths yet.",
        "action": "Keep on the regular track; review again after mid-terms.",
        "rule": lambda s: True,
    },
]

SEGMENT_BY_KEY = {s["key"]: s for s in SEGMENTS}


def assign_segment(row):
    for seg in SEGMENTS:
        if seg["rule"](row):
            return seg["key"]
    return "steady"


def public_segments():
    return [{k: v for k, v in s.items() if k != "rule"} for s in SEGMENTS]
