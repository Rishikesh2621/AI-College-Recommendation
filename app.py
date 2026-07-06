from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from ai.prompt import build_counseling_prompt
from ai.recommendation_engine import CollegeRecommendationEngine
from utils.helper import (
    BRANCHES,
    CATEGORIES,
    GENDERS,
    LANGUAGES,
    coerce_student_profile,
    markdown_to_html,
    validate_student_profile,
)
from utils.pdf_generator import build_pdf_report

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "database" / "colleges.csv"
SCHOLARSHIP_PATH = BASE_DIR / "database" / "scholarships.csv"
REPORT_DIR = BASE_DIR / "reports"
REPORT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

engine = CollegeRecommendationEngine(DATASET_PATH, SCHOLARSHIP_PATH)


@app.context_processor
def inject_form_options():
    dataset_filters = engine.filter_options()
    return {
        "categories": CATEGORIES,
        "branches": dataset_filters.get("branches") or BRANCHES,
        "colleges": dataset_filters.get("colleges") or [],
        "genders": GENDERS,
        "languages": LANGUAGES,
        "current_year": datetime.now().year,
    }


@app.route("/")
def index():
    stats = engine.get_dataset_stats()
    return render_template("index.html", stats=stats)



@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if request.method == "GET":
        return render_template("dashboard.html", errors={}, form={})

    profile = coerce_student_profile(request.form)
    errors = validate_student_profile(profile)
    if errors:
        return render_template("dashboard.html", errors=errors, form=profile), 400

    recommendations = engine.recommend(profile)
    counseling_markdown = generate_counseling(profile, recommendations)
    counseling_html = markdown_to_html(counseling_markdown)
    report_id = str(uuid.uuid4())
    pdf_path = REPORT_DIR / f"college-counseling-{report_id}.pdf"
    build_pdf_report(pdf_path, profile, recommendations, counseling_markdown)

    result_payload = {
        "profile": profile,
        "recommendations": recommendations,
        "counseling_html": counseling_html,
        "counseling_markdown": counseling_markdown,
        "report_id": report_id,
        "charts": engine.chart_payload(recommendations),
        "filters": engine.filter_options(),
    }
    return render_template("result.html", **result_payload)


@app.route("/report/<report_id>")
def download_report(report_id: str):
    safe_id = "".join(ch for ch in report_id if ch.isalnum() or ch == "-")
    report_path = REPORT_DIR / f"college-counseling-{safe_id}.pdf"
    if not report_path.exists():
        flash("Report not found. Please generate a fresh recommendation report.", "warning")
        return redirect(url_for("dashboard"))
    return send_file(report_path, as_attachment=True, download_name="college-counseling-report.pdf")


@app.route("/api/filters")
def api_filters():
    filters = {
        "city": request.args.get("city", ""),
        "branch": request.args.get("branch", ""),
        "max_fees": request.args.get("max_fees", ""),
        "min_placement": request.args.get("min_placement", ""),
        "naac_grade": request.args.get("naac_grade", ""),
        "hostel": request.args.get("hostel", ""),
        "category": request.args.get("category", ""),
    }
    percentile_str = request.args.get("percentile", "")
    percentile = None
    if percentile_str:
        try:
            percentile = float(percentile_str)
        except ValueError:
            pass

    results = engine.search(filters, percentile)
    return app.response_class(
        response=json.dumps(results, default=str),
        status=200,
        mimetype="application/json",
    )


def generate_counseling(profile: dict, recommendations: dict) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Indian engineering admissions counselor.",
                    },
                    {"role": "user", "content": build_counseling_prompt(profile, recommendations)},
                ],
                temperature=0.35,
                max_tokens=1200,
            )
            return response.choices[0].message.content or engine.fallback_counseling(profile, recommendations)
        except Exception:
            return engine.fallback_counseling(profile, recommendations)
    return engine.fallback_counseling(profile, recommendations)


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_ENV") == "development")
