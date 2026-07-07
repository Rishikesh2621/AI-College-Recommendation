# College Recommendation and Counseling Report Generator

A production-ready Flask web application that recommends engineering colleges from student profile data, previous MHT-CET cutoff records, preferences, fees, placement metrics, and hostel or scholarship needs.

## The Problem Solved (For Future Growth Foundation)

**Future Growth Foundation** is an educational counseling initiative that guides students toward optimal college admissions. 

Previously, counselors had to **manually scroll through hundreds of pages of MHT-CET CAP round cutoff PDFs** to match a student's score, category, and preferred branches/cities with suitable institutions. This manual process was slow, labor-intensive, and prone to human oversight.

**This application completely automates and solves that problem by:**
1. **Instant Cutoff Lookup:** Automatically scanning thousands of CAP-IV allotment data rows in milliseconds.
2. **Quality-Aware Matches:** Recommending the best possible options sorted by cutoff standards rather than safety choices.
3. **Interactive Visualizations:** Displaying fee, placement, and probability analytics side-by-side.
4. **Branded Report Generation:** Creating clean, print-ready PDF counseling reports containing structured tips, Parent & Authorized signatures, and custom brand letterheads instantly.

## Features

- Premium landing page with responsive Bootstrap 5 UI
- Multi-step student input form with validation
- CSV-backed recommendation engine using official CET CAP-IV allotment data for Nagpur, Amravati, Pune, Mumbai, and Nashik institutes
- Top, dream, and backup college recommendations
- Admission probability scoring based on percentile and closing cutoff difference
- OpenAI GPT counseling module with local rule-based fallback
- Dashboard with Chart.js visualizations
- Downloadable professional PDF counseling report
- Search and filters for city, branch, accreditation label, hostel, fees, and placement fields
- SQLite database starter module for future inquiry storage
- Render and Railway deployment-ready structure

## Tech Stack

- Python 3.12+
- Flask
- SQLite
- Bootstrap 5
- Chart.js
- OpenAI API
- ReportLab

## Setup

```bash
cd AI-College-Recommendation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open `http://127.0.0.1:5000`.

## OpenAI Configuration

The application works without an API key using the rule-based counseling fallback.

To enable GPT counseling, add an API key to `.env`:

```bash
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

## Dataset

The main dataset is stored at `database/colleges.csv`. It was generated from the official CET institute-wise allotment page:

`https://fe2025.mahacet.org/StaticPages/frmInstituteWiseAllotmentList?did=2021`

Included cities:

- Nagpur
- Amravati
- Pune
- Mumbai
- Nashik

The generated dataset contains 140 institutes and 3,135 official CAP-IV closing-score rows by institute, branch, and mapped category.

Columns include:

- College Name
- City
- State
- Branch
- Category
- Closing Percentile / closing score
- Fees
- Placement Percentage
- Average Package
- Highest Package
- Hostel
- NAAC Grade
- NBA
- Website
- Admission Process

`database/cutoffs.csv` provides a compact official closing-score export, `database/institutes.csv` stores the filtered official institute list, and `database/scholarships.csv` powers scholarship matching.

The official CET allotment page does not publish institute fees, hostel, placement, NAAC, or NBA values. Those fields are kept in the CSV for app compatibility and display as “Not provided” in the UI/PDF when unavailable.

## Recommendation Logic

The engine filters by category, branch, city, percentile, and hostel preference. It then ranks colleges using:

- Admission probability
- Official closing score
- Lower fees

Admission chance examples:

- Student percentile 96, cutoff 95: High or Very High
- Student percentile 92, cutoff 94: Medium
- Student percentile 88, cutoff 95: Low

## Deployment

For Render or Railway, set:

```bash
gunicorn app:app
```

Recommended environment variables:

```bash
SECRET_KEY=strong-random-secret
OPENAI_API_KEY=optional
OPENAI_MODEL=gpt-4o-mini
```

## Project Structure

```text
AI-College-Recommendation/
  app.py
  requirements.txt
  README.md
  .env.example
  ai/
  database/
  models/
  static/
  templates/
  utils/
  instance/
  uploads/
  reports/
```

## Disclaimer

This application uses official CET CAP-IV allotment data for the included city filter, but students must still verify final official cutoff lists, seat matrix, fees, accreditation, institute approvals, and admission notices before making final decisions.
