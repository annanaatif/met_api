from django.urls import path
from . import views

urlpatterns = [
    # Frontend (Template)
    path("dashboard/", views.dashboard, name="met-dashboard"),

    # APIs
    path("api/regions/", views.RegionList.as_view(), name="region-list"),
    path("api/monthly/", views.MonthlySeriesList.as_view(), name="monthly-series-list"),
    path(
        "api/monthly-pack/<str:region_code>/<str:parameter>/<int:year>/",
        views.monthly_pack_for_year,
        name="monthly-pack-for-year",
    ),
    path(
        "api/monthly-pack/<str:region_code>/<str:parameter>/",
        views.monthly_pack_all_years,
        name="monthly-pack-all-years",
    ),
]
