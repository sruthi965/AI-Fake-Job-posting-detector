from app.database import repository
from app.database.connection import check_connection, init_db

INDICATORS = [{"code": "upfront_payment", "label": "Requests upfront payment or fees", "severity": "high", "evidence": "registration fee"}]


def make_analysis(**overrides):
    data = {
        "job_title": "Data Entry Assistant", "company_name": "Global Solutions Inc.", "description": "x" * 40,
        "requirements": None, "employment_type": "Full-time", "salary_range": "$500 per week",
        "prediction": "Fraudulent", "fraud_probability": 78.0, "risk_indicators": INDICATORS,
        "explanation": None, "model_used": "logistic_regression",
    }
    data.update(overrides)
    return data


def setup_user(email="u@example.com"):
    init_db()
    return repository.create_user("Test User", email, "hash")


def test_connection_and_schema():
    init_db()
    assert check_connection()


def test_save_and_fetch_roundtrip():
    uid = setup_user()
    aid = repository.save_analysis(uid, make_analysis())
    item = repository.get_analysis(aid, uid)
    assert item["job_title"] == "Data Entry Assistant"
    assert item["fraud_probability"] == 78.0
    assert item["risk_indicators"][0]["code"] == "upfront_payment"
    assert item["explanation"] is None


def test_users_cannot_read_each_others_analyses():
    alice, bob = setup_user("a@example.com"), repository.create_user("Bob", "b@example.com", "hash")
    aid = repository.save_analysis(alice, make_analysis())
    assert repository.get_analysis(aid, bob) is None
    assert repository.delete_analysis(aid, bob) is False
    assert repository.update_explanation(aid, bob, {"summary": "x"}) is False
    assert repository.get_analysis(aid, alice) is not None


def test_pagination_orders_newest_first():
    uid = setup_user()
    for n in range(12):
        repository.save_analysis(uid, make_analysis(job_title=f"Job {n}"))
    first, total = repository.list_analyses(uid, 1, 5)
    second, _ = repository.list_analyses(uid, 2, 5)
    assert total == 12 and len(first) == 5 and len(second) == 5
    assert first[0]["job_title"] == "Job 11" and second[0]["job_title"] == "Job 6"


def test_explanation_update_and_stats():
    uid = setup_user()
    a = repository.save_analysis(uid, make_analysis())
    repository.save_analysis(uid, make_analysis(prediction="Legitimate", fraud_probability=20.0))
    assert repository.update_explanation(a, uid, {"summary": "s", "reasons": [], "recommendation": "r", "source": "template"})
    assert repository.get_analysis(a, uid)["explanation"]["summary"] == "s"
    stats = repository.user_stats(uid)
    assert stats == {"total_analyses": 2, "fraudulent": 1, "legitimate": 1, "average_probability": 49.0}


def test_stats_for_empty_history():
    uid = setup_user()
    assert repository.user_stats(uid)["total_analyses"] == 0


def test_sql_injection_text_is_stored_literally():
    uid = setup_user()
    nasty = "'); DROP TABLE job_analysis; --"
    aid = repository.save_analysis(uid, make_analysis(job_title=nasty))
    assert repository.get_analysis(aid, uid)["job_title"] == nasty
    assert repository.list_analyses(uid, 1, 10)[1] == 1
