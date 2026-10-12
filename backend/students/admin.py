from django.contrib import admin

from .models import PipelineRun, Student, SubjectPerformance


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("roll_no", "name", "department", "year", "success_score", "risk_level", "segment")
    list_filter = ("department", "year", "risk_level", "segment")
    search_fields = ("roll_no", "name")


admin.site.register(SubjectPerformance)
admin.site.register(PipelineRun)
