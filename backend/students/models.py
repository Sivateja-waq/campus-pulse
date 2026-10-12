from django.db import models


class Student(models.Model):
    roll_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    department = models.CharField(max_length=10)
    year = models.PositiveSmallIntegerField()

    # cleaned indicators coming out of the integration step
    cgpa = models.FloatField()
    backlogs = models.PositiveSmallIntegerField(default=0)
    attendance_pct = models.FloatField()
    logins_per_week = models.FloatField()
    assignment_completion = models.FloatField()
    clubs = models.PositiveSmallIntegerField(default=0)
    events = models.PositiveSmallIntegerField(default=0)
    hackathons = models.PositiveSmallIntegerField(default=0)
    certifications = models.PositiveSmallIntegerField(default=0)
    aptitude = models.FloatField(null=True, blank=True)
    coding = models.FloatField(null=True, blank=True)
    mock_interview = models.FloatField(null=True, blank=True)
    technical_skill = models.FloatField()
    soft_skill = models.FloatField()
    satisfaction = models.FloatField()
    faculty_rating = models.FloatField()

    # computed by the pipeline
    components = models.JSONField(default=dict)
    success_score = models.FloatField(default=0)
    baseline_score = models.FloatField(default=0)
    contributions = models.JSONField(default=dict)
    academic_risk = models.FloatField(default=0)
    placement_risk = models.FloatField(null=True, blank=True)
    academic_factors = models.JSONField(default=list)
    placement_factors = models.JSONField(default=list)
    risk_level = models.CharField(max_length=10, default="Low")
    flags = models.JSONField(default=list)
    segment = models.CharField(max_length=40, blank=True)
    recommendations = models.JSONField(default=list)
    attendance_trend = models.JSONField(default=list)
    lms_trend = models.JSONField(default=list)

    class Meta:
        ordering = ["roll_no"]

    def __str__(self):
        return f"{self.roll_no} {self.name}"


class SubjectPerformance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="subjects")
    subject = models.CharField(max_length=80)
    marks = models.FloatField(null=True, blank=True)
    attendance_pct = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["subject"]


class PipelineRun(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    report = models.JSONField(default=dict)   # what happened to each source file
    summary = models.JSONField(default=dict)  # model metrics + cohort insights

    class Meta:
        ordering = ["-created_at"]
