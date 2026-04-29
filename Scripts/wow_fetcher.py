import requests

PPL_BASE = "http://cawd2.nsavant.com.au/api"


def create_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "WOW-Report/1.0"})
    return s


def login(session, username, password):
    resp = session.get(f"{PPL_BASE}/login/{username}/{password}", timeout=30)
    resp.raise_for_status()
    text = resp.text.strip().lower()
    try:
        return resp.json() is True
    except Exception:
        return text == "true"


def list_paddocks(session):
    resp = session.get(f"{PPL_BASE}/paddock/", timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_weights(session, paddock_id, start_date, end_date):
    """Fetch cleansed/validated weight records."""
    resp = session.get(
        f"{PPL_BASE}/data/cleansed/{paddock_id}/{start_date}/{end_date}",
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_growth(session, paddock_id, start_date, end_date):
    """Fetch polynomial regression growth records."""
    resp = session.get(
        f"{PPL_BASE}/data/reported/{paddock_id}/{start_date}/{end_date}",
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()
