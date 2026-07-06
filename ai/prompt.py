from __future__ import annotations


def build_counseling_prompt(profile: dict, recommendations: dict) -> str:
    top = recommendations.get("top", [])[:10]
    backups = recommendations.get("backup", [])[:5]
    dreams = recommendations.get("dream", [])[:5]
    return f"""
Create a student-friendly engineering admission counseling report in Markdown.

Student profile:
- Name: {profile.get("full_name")}
- Percentile: {profile.get("percentile")}
- Category: {profile.get("category")}
- Gender: {profile.get("gender")}
- Preferred language: {profile.get("language")}
- City preference: {profile.get("city")}
- College preference: {profile.get("college")}
- Branch preference: {profile.get("branch")}
- Hostel required: {profile.get("hostel")}
- Scholarship required: {profile.get("scholarship")}

Top colleges:
{top}

Backup colleges:
{backups}

Dream colleges:
{dreams}

Include these sections:
Student Profile Summary, Academic Strength, Best Colleges, Branch Analysis,
Backup Options, Scholarship Suggestions, Counseling Tips, Mistakes to Avoid,
Final Recommendation.
Keep it practical, clear, and suitable for Indian CAP/CET counseling.
""".strip()
