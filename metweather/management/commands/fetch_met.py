import re
import requests
from django.core.management.base import BaseCommand
from metweather.models import Region, MonthlySeries, Parameter

BASE = "https://www.metoffice.gov.uk/pub/data/weather/uk/climate/datasets"

# Region code => display name (DB uses 'code' as-is)
REGIONS = {
    "UK": "United Kingdom",
    "England": "England",
    "Wales": "Wales",
    "Scotland": "Scotland",
    "Northern_Ireland": "Northern Ireland",
    "England_and_Wales": "England & Wales",
    "England_N": "England North",
    "England_S": "England South",
    "Scotland_N": "Scotland North",
    "Scotland_E": "Scotland East",
    "Scotland_W": "Scotland West",
    "England_E_and_NE": "England E & NE",
    "England_NW_and_N_Wales": "England NW/Wales N",
    "Midlands": "Midlands",
    "East_Anglia": "East Anglia",
    "England_SW_and_S_Wales": "England SW/Wales S",
    "England_SE_and_Central_S": "England SE/Central S",
}

# Met Office folder structure (left) and mapping to your model choices (right)
PARAM_TO_PATH = {
    "Tmax": "Tmax/date",
    "Tmin": "Tmin/date",
    "Tmean": "Tmean/date",
    "Sunshine": "Sunshine/date",
    "Rainfall": "Rainfall/date",
    "Raindays1mm": "Raindays1mm/date",
    "AirFrost": "AirFrost/date",
}

# File param key -> your model Parameter value
PARAM_MAP = {
    "Tmax": Parameter.TMAX,
    "Tmin": Parameter.TMIN,
    "Tmean": Parameter.TMEAN,
    "Sunshine": Parameter.SUN,
    "Rainfall": Parameter.RAIN,
    "Raindays1mm": Parameter.RAINDAYS,
    "AirFrost": Parameter.FROSTDAYS,
}

MONTH_COUNT = 12


def _tok_to_float(tok: str):
    if tok in ("", "-", "NaN"):
        return None
    tok = tok.replace("*", "")
    try:
        return float(tok)
    except Exception:
        return None


def parse_12_months(text: str):
    """
    Parse Met Office lines: YEAR, 12 monthly values, (then seasonal/annual we ignore).
    Returns dict year -> [12 monthly floats or None]
    """
    data = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        parts = re.split(r"\s+", line)
        if not parts:
            continue
        try:
            year = int(parts[0])
        except ValueError:
            continue

        month_tokens = parts[1:1 + MONTH_COUNT]
        if len(month_tokens) < MONTH_COUNT:
            continue

        months = [_tok_to_float(tok) for tok in month_tokens[:MONTH_COUNT]]
        data[year] = months
    return data


class Command(BaseCommand):
    help = "Fetch Met Office datasets and populate MonthlySeries (Jan..Dec). Skips missing files."

    def handle(self, *args, **kwargs):
        for code, name in REGIONS.items():
            region_obj, _ = Region.objects.get_or_create(
                code=code.replace(" ", "_"),
                defaults={"name": name},
            )

            for param_key, path in PARAM_TO_PATH.items():
                # Try a few filename variants; skip 404s gracefully
                urls_to_try = [
                    f"{BASE}/{path}/{code}.txt",
                    f"{BASE}/{path}/{code.replace(' ', '_')}.txt",
                    f"{BASE}/{param_key}/date/{code}.txt",
                    f"{BASE}/{param_key}/date/{code.replace(' ', '_')}.txt",
                    # Known Northern Ireland variant often needed:
                    f"{BASE}/{path}/Northern_Ireland.txt" if code in ["N_Ireland", "Northern_Ireland"] else None,
                ]
                urls_to_try = [u for u in urls_to_try if u]

                text = None
                for url in urls_to_try:
                    try:
                        r = requests.get(url, timeout=20)
                        if r.status_code == 200 and r.text.strip():
                            text = r.text
                            self.stdout.write(self.style.SUCCESS(f"Fetched {url}"))
                            break
                        elif r.status_code == 404:
                            self.stdout.write(self.style.WARNING(f"Skip 404: {url}"))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"Failed {url}: {e}"))

                if not text:
                    self.stdout.write(self.style.ERROR(f"No dataset for {code} {param_key}"))
                    continue

                by_year = parse_12_months(text)
                created = updated = 0

                model_param = PARAM_MAP.get(param_key)
                if not model_param:
                    self.stdout.write(self.style.ERROR(f"Param not mapped: {param_key}"))
                    continue

                for year, months in by_year.items():
                    for idx, val in enumerate(months, start=1):  # 1..12
                        _, was_created = MonthlySeries.objects.update_or_create(
                            region=region_obj,
                            parameter=model_param,
                            year=year,
                            month=idx,
                            defaults={"value": val},
                        )
                        if was_created:
                            created += 1
                        else:
                            updated += 1

                self.stdout.write(
                    f"{region_obj.code} {param_key}: upserted {created + updated} rows "
                    f"(created {created}, updated {updated})"
                )
