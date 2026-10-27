"""Rule-based warning indicators.

These checks are transparent heuristics that sit next to the machine learning model. They look for
well-known scam patterns and quote the matching text from the posting as evidence. They are
estimates, not proof, and the salary check only understands amounts written in US dollars.
"""
from __future__ import annotations

import re

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
SEVERITY_WEIGHT = {"high": 0.28, "medium": 0.14, "low": 0.06}
BASE_SCORE = 0.08

GENERIC_COMPANY_NAMES = {
    "confidential", "private", "anonymous", "unknown", "n/a", "na", "none", "company",
    "hiring company", "our company", "not disclosed", "undisclosed", "tbd",
}

_I = re.IGNORECASE
UPFRONT_PAYMENT = re.compile(
    r"(registration|application|processing|training|administrative|security|starter[\s-]?kit|"
    r"equipment|background[\s-]check|verification|onboarding)\s+(fee|deposit|charge|payment|cost)s?"
    r"|pay(ing)?\s+(a\s+|an\s+)?(small\s+|one[\s-]time\s+|refundable\s+)?(fee|deposit)"
    r"|(required|need|have|must)\s+to\s+pay|send\s+(us\s+)?(money|payment)|wire\s+transfer"
    r"|western\s+union|money\s?gram|gift\s*cards?|bitcoin|crypto(currency)?"
    r"|purchase\s+(your\s+own\s+)?(equipment|laptop|software|supplies)|cash(ing)?\s+(the|a)\s+check"
    r"|deposit\s+the\s+check|re-?ship(ping)?",
    _I,
)
PERSONAL_INFO = re.compile(
    r"social\s+security|\bssn\b|bank\s+(account|details|login)|routing\s+number|"
    r"(copy|scan|photo)\s+of\s+(your\s+)?(id|passport|driver)|passport\s+(copy|scan)|"
    r"(credit|debit)\s+card(\s+number)?|card\s+number",
    _I,
)
CONTACT_CHANNEL = re.compile(
    r"whatsapp|telegram|signal\s+app|hangouts|text\s+us\s+at|"
    r"[\w.+-]+@(gmail|yahoo|outlook|hotmail|aol|proton(mail)?|mail)\.(com|me)",
    _I,
)
URGENCY = re.compile(
    r"apply\s+(now|immediately|today)|limited\s+(slots|positions|openings|spots)|urgent(ly)?\s+hiring|"
    r"immediate\s+start|hiring\s+immediately|start\s+(today|immediately)|act\s+fast|only\s+\d+\s+(spots|positions|slots)",
    _I,
)
TOO_GOOD = re.compile(
    r"no\s+experience(\s+(needed|required|necessary))?|no\s+(interview|resume|skills)|"
    r"guaranteed\s+(income|pay|salary|earnings)|easy\s+(money|work|income|job)|unlimited\s+earning|"
    r"be\s+your\s+own\s+boss|earn\s+(up\s+to\s+)?\$?\d[\d,]*\s*(/|per|a)\s*(day|week|hour)\s+from\s+home",
    _I,
)
VAGUE_PHRASES = re.compile(
    r"various\s+(tasks|duties)|general\s+(duties|tasks)|simple\s+(tasks|work)|"
    r"help\s+with\s+(our\s+)?(online\s+)?(operations|business|tasks)|online\s+operations|"
    r"assist\s+with\s+(various|daily)|other\s+duties",
    _I,
)
LOW_SKILL = re.compile(
    r"data\s+entry|typing|no\s+experience|basic\s+computer|copy[\s-]?paste|survey|ad\s+posting|"
    r"envelope|package\s+(handler|forwarding)|mystery\s+shopper|assembly\s+at\s+home|reship",
    _I,
)

_AMOUNT = re.compile(r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*(k)?(?:\s*(?:-|–|—|to)\s*\$?\s*(\d[\d,]*(?:\.\d+)?)\s*(k)?)?", _I)
_PERIODS = [
    (re.compile(r"(?:per|/|\ba|each)\s*(?:hour|hr)\b|hourly", _I), 2080),
    (re.compile(r"(?:per|/|\ba|each)\s*day\b|daily", _I), 260),
    (re.compile(r"(?:per|/|\ba|each)\s*(?:week|wk)\b|weekly", _I), 52),
    (re.compile(r"(?:per|/|\ba|each)\s*month\b|monthly", _I), 12),
    (re.compile(r"(?:per|/|\ba|each)\s*(?:year|yr)\b|annual|yearly", _I), 1),
]


def _number(raw: str, thousands: str | None) -> float:
    value = float(raw.replace(",", ""))
    return value * 1000 if thousands else value


def estimate_hourly_pay(text: str | None) -> float | None:
    """Return the highest hourly-equivalent pay found in US-dollar amounts, or None."""
    if not text:
        return None
    best: float | None = None
    for match in _AMOUNT.finditer(text):
        values = [_number(match.group(1), match.group(2))]
        if match.group(3):
            values.append(_number(match.group(3), match.group(4)))
        tail = text[match.end(): match.end() + 25]
        multiplier = next((m for pattern, m in _PERIODS if pattern.search(tail)), None)
        if multiplier is None:
            if max(values) < 1000:
                continue  # an amount with no period, e.g. "$50 fee", is not a salary
            multiplier = 1
        hourly = max(values) * multiplier / 2080
        best = hourly if best is None else max(best, hourly)
    return best


def _evidence(match: re.Match | None) -> str | None:
    return match.group(0).strip()[:80] if match else None


def _indicator(code: str, label: str, severity: str, evidence: str | None = None) -> dict:
    return {"code": code, "label": label, "severity": severity, "evidence": evidence}


def analyze_risks(job: dict) -> list[dict]:
    title = job.get("job_title") or ""
    company = (job.get("company_name") or "").strip()
    description = job.get("description") or ""
    requirements = job.get("requirements") or ""
    salary = job.get("salary_range") or ""
    body = f"{description}\n{requirements}"
    found: list[dict] = []

    if m := UPFRONT_PAYMENT.search(body):
        found.append(_indicator("upfront_payment", "Requests upfront payment or fees", "high", _evidence(m)))
    if m := PERSONAL_INFO.search(body):
        found.append(_indicator("personal_info", "Asks for sensitive personal or financial details", "high", _evidence(m)))

    if not company or company.lower() in GENERIC_COMPANY_NAMES:
        found.append(_indicator("company_info", "Company information is incomplete or unverifiable", "medium",
                                company or "No company name provided"))

    words = len(description.split())
    vague = VAGUE_PHRASES.search(description)
    if words < 30 or vague:
        found.append(_indicator("vague_description", "Job description contains vague responsibilities", "medium",
                                _evidence(vague) or f"Only {words} words describe the role"))

    hourly = estimate_hourly_pay(salary) or estimate_hourly_pay(description)
    if hourly and LOW_SKILL.search(f"{title} {body}") and hourly >= 20:
        found.append(_indicator("unrealistic_salary", "Unrealistic salary for the listed role", "medium",
                                f"Listed pay is about ${hourly:.0f} per hour for a role with minimal requirements"))

    if m := TOO_GOOD.search(body):
        found.append(_indicator("too_good", "Promises easy work or guaranteed income", "medium", _evidence(m)))
    if m := CONTACT_CHANNEL.search(body):
        found.append(_indicator("contact_channel", "Uses a personal email or chat app for contact", "medium", _evidence(m)))
    if m := URGENCY.search(body):
        found.append(_indicator("urgency", "Pressures you to act quickly", "low", _evidence(m)))

    found.sort(key=lambda i: SEVERITY_ORDER[i["severity"]])
    return found


def rule_score(indicators: list[dict]) -> float:
    """Fallback fraud probability (0-1) used only when no trained model is available."""
    return min(0.97, BASE_SCORE + sum(SEVERITY_WEIGHT[i["severity"]] for i in indicators))


def risk_level(probability: float) -> str:
    """Map a probability (0-1) to a coarse level."""
    if probability < 0.3:
        return "low"
    if probability < 0.6:
        return "medium"
    return "high"
