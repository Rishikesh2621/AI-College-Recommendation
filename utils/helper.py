from __future__ import annotations

import re

import markdown

CATEGORIES = [
    "DEF-General",
    "DEF-NT1",
    "DEF-NT2",
    "DEF-NT3",
    "DEF-OBC",
    "DEF-SC",
    "DEF-SEBC",
    "DEF-ST",
    "DEF-VJ/DT",
    "EWS",
    "General",
    "MI",
    "MI-AI",
    "MI-MH",
    "NT1",
    "NT2",
    "NT3",
    "OBC",
    "ORPHAN",
    "PWD-General",
    "PWD-NT1",
    "PWD-NT2",
    "PWD-NT3",
    "PWD-OBC",
    "PWD-SC",
    "PWD-SEBC",
    "PWD-ST",
    "PWD-VJ/DT",
    "SC",
    "SEBC",
    "ST",
    "TFWS",
    "VJ/DT",
]
GENDERS = ["Male", "Female", "Other"]
LANGUAGES = ["English", "Hindi", "Marathi"]
BRANCHES = [
    "Computer Science",
    "Information Technology",
    "Artificial Intelligence",
    "Artificial Intelligence and Machine Learning",
    "Electronics",
    "Electrical",
    "Mechanical",
    "Civil",
    "Chemical",
]
YES_NO = ["Yes", "No"]


def coerce_student_profile(form) -> dict:
    branches = []
    if hasattr(form, "getlist"):
        branches = form.getlist("branches")
    
    if not branches:
        branches = form.get("branches") or []
        if isinstance(branches, str):
            branches = [branches]
    
    if not branches and form.get("branch"):
        branches = [form.get("branch")]

    branches = [b.strip() for b in branches if b.strip()]

    return {
        "full_name": form.get("full_name", "").strip(),
        "email": form.get("email", "").strip().lower(),
        "phone": re.sub(r"\D", "", form.get("phone", "")),
        "percentile": form.get("percentile", "").strip(),
        "category": form.get("category", "").strip(),
        "gender": form.get("gender", "").strip(),
        "language": form.get("language", "").strip(),
        "city": form.get("city", "").strip(),
        "college": form.get("college", "").strip(),
        "branches": branches,
        "hostel": form.get("hostel", "No").strip() or "No",
        "scholarship": form.get("scholarship", "No").strip() or "No",
    }


def validate_student_profile(profile: dict) -> dict:
    errors = {}
    required = {
        "full_name": "Full name is required.",
        "email": "Email address is required.",
        "phone": "Phone number is required.",
        "percentile": "Percentile is required.",
        "category": "Category is required.",
        "gender": "Gender is required.",
        "language": "Preferred language is required.",
    }

    for key, message in required.items():
        if not profile.get(key):
            errors[key] = message

    if not profile.get("branches"):
        errors["branches"] = "Preferred branch is required."
    elif len(profile["branches"]) > 6:
        errors["branches"] = "Select a maximum of 6 branches."

    if profile.get("email") and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", profile["email"]):
        errors["email"] = "Enter a valid email address."

    if profile.get("phone") and not re.match(r"^\d{10}$", profile["phone"]):
        errors["phone"] = "Enter a valid 10-digit phone number."

    try:
        percentile = float(profile.get("percentile", ""))
        if percentile < 0 or percentile > 100:
            errors["percentile"] = "Percentile must be between 0 and 100."
    except ValueError:
        errors["percentile"] = "Percentile must be a number between 0 and 100."

    if profile.get("category") and profile["category"] not in CATEGORIES:
        errors["category"] = "Choose a valid category."
    if profile.get("gender") and profile["gender"] not in GENDERS:
        errors["gender"] = "Choose a valid gender."
    if profile.get("language") and profile["language"] not in LANGUAGES:
        errors["language"] = "Choose a valid language."

    return errors


def markdown_to_html(text: str) -> str:
    return markdown.markdown(text, extensions=["tables", "sane_lists"])


def money(value: float | int) -> str:
    if float(value) <= 0:
        return "—"
    return f"Rs. {int(value):,}"
