from django.urls import path

from . import views

urlpatterns = [
    path("meta/", views.meta),
    path("overview/", views.overview),
    path("students/", views.student_list),
    path("students/<str:roll_no>/", views.student_detail),
    path("segments/", views.segments),
    path("data/", views.data_report),
    path("data/rerun/", views.rerun),
    path("data/upload/<str:source>/", views.upload_source),
]
