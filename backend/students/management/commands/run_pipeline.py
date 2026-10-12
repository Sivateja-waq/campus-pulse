from django.core.management.base import BaseCommand

from students.analytics.pipeline import run
from students.models import Student


class Command(BaseCommand):
    help = "Integrate the raw CSVs, score every student and load the results"

    def handle(self, *args, **opts):
        result = run()
        self.stdout.write(f"Loaded {Student.objects.count()} students")
        for m in result.summary["models"]:
            self.stdout.write(f"  {m['name']}: held-out AUC {m['auc']}")
        for line in result.summary["insights"]:
            self.stdout.write(f"  - {line}")
        self.stdout.write(self.style.SUCCESS("Done"))
