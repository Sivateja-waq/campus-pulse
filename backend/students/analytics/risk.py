"""
Two risk models trained on last batch's outcomes (alumni_outcomes.csv):

  academic risk  - did the student end up with serious academic trouble
  placement risk - did the student finish without a placement

Plain logistic regression on standardised features. We picked it over a
fancier model on purpose: coefficient * standardised value is a direct,
honest measure of how much each indicator pushes one student's risk up or
down, so faculty can see *why* someone was flagged.
"""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

FEATURE_LABELS = {
    "cgpa": "CGPA",
    "backlogs": "Active backlogs",
    "attendance_pct": "Attendance",
    "assignment_completion": "Assignment completion",
    "logins_per_week": "LMS logins",
    "aptitude": "Aptitude score",
    "coding": "Coding score",
    "mock_interview": "Mock interview",
    "technical_skill": "Technical skills",
    "soft_skill": "Soft skills",
    "certifications": "Certifications",
    "hackathons": "Hackathons",
}

ACADEMIC_FEATURES = ["cgpa", "backlogs", "attendance_pct", "assignment_completion", "logins_per_week"]
PLACEMENT_FEATURES = ["cgpa", "backlogs", "aptitude", "coding", "mock_interview",
                      "technical_skill", "soft_skill", "certifications", "hackathons"]


class RiskModel:
    def __init__(self, name, features, target):
        self.name = name
        self.features = features
        self.target = target
        self.pipe = None
        self.auc = None

    def fit(self, alumni):
        X = alumni[self.features].fillna(0)
        y = alumni[self.target]
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=7, stratify=y)
        self.pipe = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        self.pipe.fit(X_tr, y_tr)
        self.auc = float(roc_auc_score(y_te, self.pipe.predict_proba(X_te)[:, 1]))
        # held-out check done, now use all of last year's data
        self.pipe.fit(X, y)
        return self

    def predict(self, df):
        X = df[self.features].fillna(0)
        proba = self.pipe.predict_proba(X)[:, 1]
        scaler, lr = self.pipe[0], self.pipe[-1]
        contrib = scaler.transform(X) * lr.coef_[0]
        return proba, contrib

    def top_factors(self, contrib_row, n=3):
        """Indicators pushing this student's risk up the most (in log-odds)."""
        ranked = sorted(zip(self.features, contrib_row), key=lambda p: -p[1])
        return [{"feature": f, "label": FEATURE_LABELS[f], "impact": round(float(v), 2)}
                for f, v in ranked[:n] if v > 0.1]

    def describe(self):
        lr = self.pipe[-1]
        weights = sorted(zip(self.features, lr.coef_[0]), key=lambda p: -abs(p[1]))
        return {
            "name": self.name,
            "auc": round(self.auc, 3),
            "trained_on": self.target,
            "coefficients": [{"feature": FEATURE_LABELS[f], "weight": round(float(w), 3)} for f, w in weights],
        }


def level(prob):
    if prob is None or np.isnan(prob):
        return None
    if prob >= 0.55:
        return "High"
    if prob >= 0.30:
        return "Medium"
    return "Low"
