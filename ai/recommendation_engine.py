from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


class CollegeRecommendationEngine:
    def __init__(self, colleges_path: Path, scholarships_path: Path):
        self.colleges_path = colleges_path
        self.scholarships_path = scholarships_path

    def load_colleges(self) -> list[dict]:
        with self.colleges_path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))
        return [self._normalize(row) for row in rows]

    def load_scholarships(self) -> list[dict]:
        if not self.scholarships_path.exists():
            return []
        with self.scholarships_path.open(newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))

    def recommend(self, profile: dict) -> dict:
        percentile = float(profile["percentile"])
        city_input = profile.get("city", "").strip()
        preferred_cities = [c.strip().lower() for c in city_input.split(",") if c.strip()]
        branch = profile.get("branch", "")
        category = profile.get("category", "")
        rows = self.load_colleges()
        # Filter by Category and Branch, but keep all cities
        # so we can prioritize the preferred city and suggest other cities below it.
        filtered = [
            college
            for college in rows
            if college["Category"] == category
            and college["Branch"] == branch
        ]

        if len(filtered) < 10:
            filtered = [
                college
                for college in rows
                if college["Category"] == category
            ]
        if len(filtered) < 10:
            filtered = [
                college
                for college in rows
                if college["Branch"] == branch
            ]
        if len(filtered) < 10:
            filtered = rows

        scored = [self._score(college, percentile) for college in filtered]
        
        # Deduplicate scored list to keep only the highest scored option for each (College Name, Branch)
        deduped_scored = []
        seen_colleges = set()
        for item in sorted(scored, key=lambda x: x["admission_score"], reverse=True):
            key = (item["College Name"], item["Branch"])
            if key not in seen_colleges:
                seen_colleges.add(key)
                deduped_scored.append(item)
        
        def city_priority(item_city):
            if not preferred_cities:
                return 0
            item_city_lower = item_city.lower()
            if item_city_lower in preferred_cities:
                return len(preferred_cities) - preferred_cities.index(item_city_lower)
            return 0

        def city_priority_asc(item_city):
            if not preferred_cities:
                return 0
            item_city_lower = item_city.lower()
            if item_city_lower in preferred_cities:
                return preferred_cities.index(item_city_lower) - len(preferred_cities)
            return 0

        all_preferences = sorted(
            deduped_scored,
            key=lambda item: (
                city_priority(item["City"]),
                item["admission_probability"],
                item["Closing Percentile"],
                item["College Name"],
            ),
            reverse=True,
        )
        
        top = sorted(
            [item for item in deduped_scored if item["Closing Percentile"] <= percentile + 4],
            key=lambda item: (
                city_priority(item["City"]),
                item["Closing Percentile"],
                item["Placement Percentage"],
                -item["Fees"],
            ),
            reverse=True,
        )[:10]
        if not top:
            top = sorted(
                deduped_scored,
                key=lambda item: (
                    city_priority(item["City"]),
                    item["Closing Percentile"],
                    item["Placement Percentage"],
                    -item["Fees"],
                ),
                reverse=True,
            )[:10]

        dream = sorted(
            [item for item in deduped_scored if item["Closing Percentile"] > percentile],
            key=lambda item: (
                city_priority_asc(item["City"]),
                item["Closing Percentile"],
                item["Placement Percentage"],
            ),
        )[:5]
        
        backup = sorted(
            [item for item in deduped_scored if item["Closing Percentile"] <= percentile],
            key=lambda item: (
                city_priority_asc(item["City"]),
                item["Fees"],
                -item["Placement Percentage"],
            ),
        )[:5]

        return {
            "top": top,
            "dream": dream or sorted(deduped_scored, key=lambda item: (city_priority_asc(item["City"]), item["Closing Percentile"]))[:5],
            "backup": backup or sorted(deduped_scored, key=lambda item: (city_priority_asc(item["City"]), item["Closing Percentile"]))[:5],
            "chance_groups": self._chance_groups(all_preferences, city_input),
            "preferred_college": self._preferred_college_matches(profile, percentile),
            "scholarships": self.match_scholarships(profile),
            "timeline": self.admission_timeline(),
        }

    def search(self, filters: dict, percentile: float | None = None) -> list[dict]:
        rows = self.load_colleges()
        results = []
        for college in rows:
            if filters.get("category") and college["Category"] != filters["category"]:
                continue
            if filters.get("city") and college["City"] != filters["city"]:
                continue
            if filters.get("branch") and college["Branch"] != filters["branch"]:
                continue
            if filters.get("max_fees") and college["Fees"] > int(filters["max_fees"]):
                continue
            if filters.get("min_placement") and college["Placement Percentage"] < int(filters["min_placement"]):
                continue
            if filters.get("naac_grade") and college["NAAC Grade"] != filters["naac_grade"]:
                continue
            if filters.get("hostel") and college["Hostel"] != filters["hostel"]:
                continue
            
            if percentile is not None:
                results.append(self._score(college, percentile))
            else:
                results.append(college)
        return results[:50]

    def chart_payload(self, recommendations: dict) -> dict:
        top = recommendations.get("top", [])
        chance_counts = Counter(item["chance"] for item in top)
        branch_counts = Counter(item["Branch"] for item in top)
        return {
            "probabilities": {"labels": list(chance_counts), "values": list(chance_counts.values())},
            "fees": {
                "labels": [item["College Name"] for item in top[:6]],
                "values": [item["Fees"] for item in top[:6]],
                "has_data": any(item["Fees"] > 0 for item in top[:6]),
            },
            "placements": {
                "labels": [item["College Name"] for item in top[:6]],
                "values": [item["Placement Percentage"] for item in top[:6]],
                "has_data": any(item["Placement Percentage"] > 0 for item in top[:6]),
            },
            "branches": {"labels": list(branch_counts), "values": list(branch_counts.values())},
            "ranking": {
                "labels": [item["College Name"] for item in top[:8]],
                "values": [round(item["admission_probability"], 1) for item in top[:8]],
            },
        }

    def filter_options(self) -> dict:
        rows = self.load_colleges()
        return {
            "cities": sorted({row["City"] for row in rows}),
            "branches": sorted({row["Branch"] for row in rows}),
            "colleges": sorted({row["College Name"] for row in rows}),
            "naac": sorted({row["NAAC Grade"] for row in rows}),
        }

    def get_dataset_stats(self) -> dict:
        rows = self.load_colleges()
        return {
            "colleges": len({row["College Name"] for row in rows}),
            "records": len(rows),
            "cities": len({row["City"] for row in rows}),
            "branches": len({row["Branch"] for row in rows}),
        }

    def match_scholarships(self, profile: dict) -> list[dict]:
        percentile = float(profile["percentile"])
        category = profile.get("category", "")
        matches = []
        for scholarship in self.load_scholarships():
            min_percentile = float(scholarship.get("Minimum Percentile", 0))
            eligible_categories = scholarship.get("Categories", "")
            if percentile >= min_percentile and (category in eligible_categories or "All" in eligible_categories):
                matches.append(scholarship)
        return matches[:5]

    def fallback_counseling(self, profile: dict, recommendations: dict) -> str:
        top = recommendations.get("top", [])
        best = top[0] if top else {}
        scholarship_names = ", ".join(item["Scholarship Name"] for item in recommendations.get("scholarships", []))
        return f"""
## Student Profile Summary
{profile["full_name"]} has scored {profile["percentile"]} percentile and is targeting {profile["branch"]} colleges under the {profile["category"]} category.

## Academic Strength
The score indicates a strong profile for practical counseling choices. Colleges with cutoffs within 2 percentile points should be treated as realistic options.

## Best Colleges
The strongest current match is **{best.get("College Name", "a suitable listed college")}** with an estimated {best.get("chance", "Medium")} admission chance.

## Branch Analysis
{profile["branch"]} remains placement-oriented, with strong opportunities in software, analytics, automation, and product engineering roles.

## Backup Options
Keep at least five lower-cutoff colleges in the option form to protect against cutoff movement.

## Scholarship Suggestions
{scholarship_names or "Check state fee concession, EWS/category benefits, merit scholarships, and institute-level aid."}

## Counseling Tips
Prioritize colleges by branch quality, placement consistency, fees, commute or hostel availability, and accreditation.

## Mistakes to Avoid
Do not fill only dream colleges. Avoid ignoring fees, hostel constraints, document deadlines, and category-specific seat rules.
## Final Recommendation
Submit a balanced preference list with dream, realistic, and backup colleges. Re-check official cutoff lists before final locking.
""".strip()

    @staticmethod
    def admission_timeline() -> list[str]:
        return [
            "Registration and document upload",
            "Document verification and grievance window",
            "Provisional merit list",
            "Option form filling",
            "Seat allotment round",
            "Seat acceptance and fee payment",
            "Institute reporting",
        ]

    @staticmethod
    def _normalize(row: dict) -> dict:
        normalized = dict(row)
        for key in ["Closing Percentile", "Fees", "Placement Percentage", "Average Package", "Highest Package"]:
            normalized[key] = float(normalized[key])
        normalized["Fees"] = int(normalized["Fees"])
        return normalized

    def _preferred_college_matches(self, profile: dict, percentile: float) -> list[dict]:
        college_name = profile.get("college", "").strip()
        if not college_name:
            return []
        branch = profile.get("branch", "")
        category = profile.get("category", "")
        college_rows = [college for college in self.load_colleges() if college["College Name"] == college_name]
        if category:
            college_rows = [college for college in college_rows if college["Category"] == category]
        matching_sets = [
            [
                college
                for college in college_rows
                if (not branch or college["Branch"] == branch)
            ],
            college_rows,
        ]
        matched_rows = next((rows for rows in matching_sets if rows), [])
        matches = [self._score(college, percentile) for college in matched_rows]
        return sorted(matches, key=lambda item: item["admission_probability"], reverse=True)

    @staticmethod
    def _chance_groups(colleges: list[dict], city: str = "") -> dict:
        groups = {"High Chance": [], "Medium Chance": [], "Low Chance": []}
        seen = {key: set() for key in groups}
        preferred_cities = [c.strip().lower() for c in city.split(",") if c.strip()] if city else []
        for college in colleges:
            if preferred_cities and college["City"].lower() not in preferred_cities:
                continue

            if college["chance"] in {"Very High", "High"}:
                group = "High Chance"
            elif college["chance"] == "Medium":
                group = "Medium Chance"
            else:
                group = "Low Chance"

            dedupe_key = (college["College Name"], college["Branch"])
            if dedupe_key in seen[group]:
                continue
            seen[group].add(dedupe_key)
            groups[group].append(college)

        def city_priority(item_city):
            if not preferred_cities:
                return 0
            item_city_lower = item_city.lower()
            if item_city_lower in preferred_cities:
                return len(preferred_cities) - preferred_cities.index(item_city_lower)
            return 0

        # Sort each group to ensure preferred city colleges come first
        for group in groups:
            groups[group] = sorted(
                groups[group],
                key=lambda item: (
                    city_priority(item["City"]),
                    item["admission_probability"],
                    item["Closing Percentile"],
                    item["College Name"],
                ),
                reverse=True,
            )
        return groups

    @staticmethod
    def _score(college: dict, percentile: float) -> dict:
        difference = percentile - college["Closing Percentile"]
        if difference >= 3:
            chance = "Very High"
            probability = min(98, 88 + difference)
        elif difference >= 0:
            chance = "High"
            probability = 76 + (difference * 4)
        elif difference >= -3:
            chance = "Medium"
            probability = 52 + ((difference + 3) * 6)
        elif difference >= -7:
            chance = "Low"
            probability = 25 + ((difference + 7) * 5)
        else:
            chance = "Very Low"
            probability = max(5, 20 + difference)

        scored = dict(college)
        scored["difference"] = round(difference, 2)
        scored["chance"] = chance
        scored["admission_probability"] = round(probability, 1)
        scored["admission_score"] = probability + (college["Placement Percentage"] * 0.18) - (college["Fees"] / 100000)
        return scored
