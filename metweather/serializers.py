from rest_framework import serializers
from .models import Region, MonthlySeries

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["code", "name"]


class MonthlySeriesSerializer(serializers.ModelSerializer):
    region = serializers.CharField(source="region.code")
    month_name = serializers.SerializerMethodField()

    class Meta:
        model = MonthlySeries
        fields = ["region", "parameter", "year", "month", "month_name", "value"]

    def get_month_name(self, obj):
        return MONTH_NAMES[obj.month - 1]


class YearlyPackSerializer(serializers.Serializer):
    region = serializers.CharField()
    parameter = serializers.CharField()
    year = serializers.IntegerField()
    months = serializers.DictField(
        child=serializers.FloatField(allow_null=True)
    )


class AllYearsPackSerializer(serializers.Serializer):
    region = serializers.CharField()
    parameter = serializers.CharField()
    data = serializers.DictField(
        child=serializers.DictField(
            child=serializers.FloatField(allow_null=True)
        )
    )
