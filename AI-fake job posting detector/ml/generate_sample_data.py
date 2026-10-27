"""Create a SYNTHETIC demo dataset so the project runs end to end without downloading anything.

    python -m ml.generate_sample_data --rows 3000

The postings are generated from templates. Metrics measured on this file say nothing about real-world
accuracy; train on the real dataset (see data/README.md) for meaningful results.
"""
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from app.core.config import BASE_DIR

ROLES = ["Software Engineer", "Marketing Associate", "Accountant", "Customer Support Specialist", "Data Analyst",
         "Nurse", "Warehouse Associate", "Graphic Designer", "Sales Executive", "HR Coordinator", "Mechanical Engineer",
         "Content Writer", "Project Manager", "Electrician", "Teacher"]
COMPANIES = ["ABC Tech", "Bright Media", "NextGen Solutions", "Northwind Logistics", "Harbor Health", "Summit Finance",
             "Blue Ridge Analytics", "Oakline Retail", "Meridian Labs", "Cedar Education", "Pioneer Motors", "Lumen Studio"]
SKILLS = ["communication", "teamwork", "problem solving", "Excel", "SQL", "Python", "project planning", "customer service",
          "technical writing", "time management", "budgeting", "Figma", "inventory systems"]
LEGIT_DUTIES = [
    "Collaborate with the {team} team to deliver quarterly goals and report progress to your manager.",
    "Maintain accurate records, prepare weekly reports and support audits.",
    "Design, build and test features, review code and take part in sprint planning.",
    "Respond to customer enquiries, resolve issues and document recurring problems.",
    "Plan campaigns, analyse results and present findings to stakeholders.",
    "Coordinate schedules, manage vendor relationships and track budgets.",
]
LEGIT_BENEFITS = ["Health insurance and paid leave are included.", "We offer a hybrid schedule and learning budget.",
                  "Apply through our careers page; shortlisted candidates are interviewed by the hiring manager."]
FRAUD_FEES = ["You will be required to pay a small registration fee of ${n} before starting.",
              "A refundable security deposit of ${n} is needed to receive your starter kit.",
              "Candidates must purchase their own equipment through our approved vendor.",
              "Pay a processing fee of ${n} to secure your position."]
FRAUD_LURES = ["No experience needed, earn ${n} per week working from home with guaranteed income.",
               "Easy work, flexible hours, unlimited earning potential. Be your own boss.",
               "We are urgently hiring and have limited slots, apply now to start immediately."]
FRAUD_VAGUE = ["Help with our online operations and various tasks assigned daily.",
               "Simple tasks such as data entry, typing and general duties.",
               "Assist with various duties as required by the business."]
FRAUD_CONTACT = ["Contact our manager on WhatsApp to begin.", "Send your details and a copy of your ID to hr.careers@gmail.com.",
                 "Message us on Telegram to receive your first assignment."]
TEAMS = ["product", "finance", "operations", "engineering", "marketing", "support"]
TYPES = ["Full-time", "Part-time", "Contract", "Temporary", "Internship"]


def legit(rng: random.Random) -> dict:
    role = rng.choice(ROLES)
    skills = ", ".join(rng.sample(SKILLS, 3))
    duties = " ".join(rng.sample(LEGIT_DUTIES, 3)).format(team=rng.choice(TEAMS))
    desc = f"{duties} {rng.choice(LEGIT_BENEFITS)}"
    company = rng.choice(COMPANIES) if rng.random() > 0.08 else ""
    salary = f"${rng.randrange(40, 140, 5)},000 per year" if rng.random() < 0.6 else ""
    if rng.random() < 0.08:  # legitimate postings can also use urgent or casual wording
        desc += " " + rng.choice(["We are hiring urgently, apply today.", "No experience needed for this entry-level role; we train you."])
    if rng.random() < 0.06:  # a legitimate but short posting
        desc = rng.choice(LEGIT_DUTIES).format(team=rng.choice(TEAMS))
    return {"title": role, "company_name": company, "description": desc,
            "requirements": f"{rng.randint(1, 6)}+ years of experience. Skills: {skills}.",
            "employment_type": rng.choice(TYPES), "salary_range": salary, "fraudulent": 0}


def fraud(rng: random.Random) -> dict:
    role = rng.choice(["Data Entry Assistant", "Remote Typist", "Package Handler", "Online Survey Agent", "Home Assembly Worker"] + ROLES[:3])
    parts = [rng.choice(FRAUD_VAGUE)]
    if rng.random() < 0.25:  # "stealthy" scams that read like ordinary postings
        parts = [rng.choice(LEGIT_DUTIES).format(team=rng.choice(TEAMS))]
    # Each scam signal appears only some of the time, so the model cannot rely on one keyword.
    for pool, chance in ((FRAUD_FEES, 0.55), (FRAUD_LURES, 0.6), (FRAUD_CONTACT, 0.45)):
        if rng.random() < chance:
            parts.append(rng.choice(pool).format(n=rng.choice([30, 50, 75, 99, 120])))
    rng.shuffle(parts)
    company = rng.choice(COMPANIES) if rng.random() < 0.35 else ""
    salary = f"${rng.choice([400, 500, 800, 1000])} - ${rng.choice([900, 1200, 1500])} per week" if rng.random() < 0.7 else ""
    return {"title": role, "company_name": company, "description": " ".join(parts),
            "requirements": rng.choice(["Basic computer skills, good communication", "No experience required", ""]),
            "employment_type": rng.choice(["Full-time", "Part-time", "Temporary"]), "salary_range": salary, "fraudulent": 1}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic demo dataset.")
    parser.add_argument("--rows", type=int, default=3000)
    parser.add_argument("--fraud-rate", type=float, default=0.12)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", default="data/sample_job_postings.csv")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = [fraud(rng) if rng.random() < args.fraud_rate else legit(rng) for _ in range(args.rows)]
    out = Path(args.out) if Path(args.out).is_absolute() else BASE_DIR / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["title", "company_name", "description", "requirements", "employment_type", "salary_range", "fraudulent", "synthetic"]
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "synthetic": 1})
    print(f"Wrote {len(rows)} synthetic rows to {out}")


if __name__ == "__main__":
    main()
