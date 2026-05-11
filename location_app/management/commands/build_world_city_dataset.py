import json
from collections import Counter
from datetime import datetime, UTC
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Build a compact worldwide city dataset from GeoNames cities500."

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            default=str(
                Path(settings.BASE_DIR)
                / "location_app"
                / "data"
                / "cities500_raw"
                / "cities500.txt"
            ),
            help="Path to the GeoNames cities500.txt file.",
        )
        parser.add_argument(
            "--output",
            default=str(Path(settings.BASE_DIR) / "location_app" / "data" / "world_cities.json"),
            help="Path to the generated JSON dataset.",
        )

    def handle(self, *args, **options):
        input_path = Path(options["input"])
        output_path = Path(options["output"])

        if not input_path.exists():
            raise CommandError(f"Input dataset not found: {input_path}")

        self.stdout.write(f"Reading {input_path} ...")
        raw_rows = []
        label_counts = Counter()

        with input_path.open("r", encoding="utf-8") as source:
            for line in source:
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 15:
                    continue

                geoname_id = int(parts[0])
                name = parts[1].strip()
                ascii_name = parts[2].strip() or name
                latitude = float(parts[4])
                longitude = float(parts[5])
                country_code = parts[8].strip()
                admin1_code = parts[10].strip()
                population = int(parts[14] or 0)

                base_label = f"{ascii_name}, {country_code}" if country_code else ascii_name
                label_counts[base_label] += 1
                raw_rows.append(
                    {
                        "id": geoname_id,
                        "name": name,
                        "ascii_name": ascii_name,
                        "country_code": country_code,
                        "admin1_code": admin1_code,
                        "lat": latitude,
                        "lng": longitude,
                        "population": population,
                        "base_label": base_label,
                    }
                )

        raw_rows.sort(key=lambda row: (-row["population"], row["base_label"], row["id"]))
        cities = []

        for row in raw_rows:
            if label_counts[row["base_label"]] > 1:
                if row["admin1_code"]:
                    label = f'{row["name"]}, {row["admin1_code"]} {row["country_code"]}'
                else:
                    label = f'{row["name"]}, {row["country_code"]} #{row["id"]}'
            else:
                label = row["base_label"]

            cities.append(
                [
                    row["id"],
                    label,
                    row["name"],
                    row["ascii_name"],
                    row["country_code"],
                    row["admin1_code"],
                    row["lat"],
                    row["lng"],
                    row["population"],
                ]
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "source": "GeoNames cities500",
            "generated_at": datetime.now(UTC).isoformat(),
            "total_cities": len(cities),
            "cities": cities,
        }

        with output_path.open("w", encoding="utf-8") as target:
            json.dump(payload, target, ensure_ascii=False, separators=(",", ":"))

        self.stdout.write(
            self.style.SUCCESS(
                f"Generated {len(cities)} city records at {output_path}"
            )
        )
