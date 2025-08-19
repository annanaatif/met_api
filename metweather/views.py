from django.shortcuts import get_object_or_404, render
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Region, MonthlySeries, Parameter
from .serializers import (
    RegionSerializer,
    MonthlySeriesSerializer,
    YearlyPackSerializer,
    AllYearsPackSerializer,
    MONTH_NAMES,
)



class RegionList(generics.ListAPIView):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class MonthlySeriesList(generics.ListAPIView):
    """
    GET /api/monthly/?region=UK&parameter=Tmax&start=1990&end=2000&month=1
    Returns flat rows; includes month_name for convenience.
    """
    serializer_class = MonthlySeriesSerializer

    def get_queryset(self):
        qs = MonthlySeries.objects.all()
        qp = self.request.query_params

        region = qp.get("region")
        parameter = qp.get("parameter")
        start = qp.get("start")
        end = qp.get("end")
        month = qp.get("month")  # optional 1..12 filter

        if region:
            qs = qs.filter(region__code__iexact=region)
        if parameter:
            qs = qs.filter(parameter__iexact=parameter)
        if start:
            qs = qs.filter(year__gte=int(start))
        if end:
            qs = qs.filter(year__lte=int(end))
        if month:
            qs = qs.filter(month=int(month))

        return qs.order_by("year", "month")


@api_view(["GET"])
def monthly_pack_for_year(request, region_code, parameter, year):
    """
    GET /api/monthly-pack/<region>/<parameter>/<year>/
    Returns month-name dict for a single year.
    """
    region = get_object_or_404(Region, code__iexact=region_code)
    rows = MonthlySeries.objects.filter(
        region=region, parameter__iexact=parameter, year=int(year)
    ).values("month", "value")

    months_dict = {name: None for name in MONTH_NAMES}
    for row in rows:
        months_dict[MONTH_NAMES[row["month"] - 1]] = row["value"]

    payload = {
        "region": region.code,
        "parameter": parameter,
        "year": int(year),
        "months": months_dict,
    }
    ser = YearlyPackSerializer(payload)
    return Response(ser.data)


@api_view(["GET"])
def monthly_pack_all_years(request, region_code, parameter):
    """
    GET /api/monthly-pack/<region>/<parameter>/
    Returns data: {year: {MonthName: value or null}}
    Optional query: ?start=YYYY&end=YYYY
    """
    region = get_object_or_404(Region, code__iexact=region_code)

    qp = request.query_params
    start = qp.get("start")
    end = qp.get("end")

    qs = MonthlySeries.objects.filter(
        region=region, parameter__iexact=parameter
    ).values("year", "month", "value")

    if start:
        qs = qs.filter(year__gte=int(start))
    if end:
        qs = qs.filter(year__lte=int(end))

    data = {}
    for row in qs:
        y = row["year"]
        if y not in data:
            data[y] = {name: None for name in MONTH_NAMES}
        data[y][MONTH_NAMES[row["month"] - 1]] = row["value"]

    payload = {
        "region": region.code,
        "parameter": parameter,
        "data": data,
    }
    ser = AllYearsPackSerializer(payload)
    return Response(ser.data)


def dashboard(request):
    """
    Simple dashboard page with dropdowns and a Chart.js visualization.
    """
    regions = Region.objects.order_by("code")
    # Build parameter choices from the enum, expose only the value (e.g. "Tmax")
    parameters = [choice[0] for choice in Parameter.choices]
    months = MONTH_NAMES

    return render(
        request,
        "metweather/dashboard.html",
        {"regions": regions, "parameters": parameters, "months": months},
    )
