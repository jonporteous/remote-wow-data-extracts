import sys
import requests
from requests.exceptions import ConnectTimeout, ConnectionError as ReqConnError

PPL_BASE = "http://cawd2.nsavant.com.au/api"

_WHITELIST_MSG = (
    "\n  Cannot reach the PPL server. Most likely causes:\n"
    "  1. Your IP address is not whitelisted for this farm.\n"
    "     - Log into PPL as 'nsavant', find the farm, edit the user,\n"
    "       add your IP to the 'API IP ACL' field.\n"
    "     - Also email BGP support to add your IP to the PPL Server Security Groups.\n"
    "  2. A VPN is active — disconnect it, as VPN changes your IP address.\n"
    "  3. The PPL server is temporarily down.\n"
    "\n"
    "  Note: the PPL web dashboard (http://cawd2.nsavant.com.au/dashboard)\n"
    "  has no IP restriction — only the API endpoints require whitelisting.\n"
)


def _get(session, url, timeout=30):
    try:
        return session.get(url, timeout=timeout)
    except (ConnectTimeout, ReqConnError):
        sys.exit(_WHITELIST_MSG)


def create_session():
    s = requests.Session()
    s.headers.update({"User-Agent": "WOW-Report/1.0"})
    return s


def login(session, username, password):
    resp = _get(session, f"{PPL_BASE}/login/{username}/{password}", timeout=60)
    resp.raise_for_status()
    text = resp.text.strip().lower()
    try:
        return resp.json() is True
    except Exception:
        return text == "true"


def list_paddocks(session):
    resp = _get(session, f"{PPL_BASE}/paddock/", timeout=60)
    resp.raise_for_status()
    return resp.json()


def fetch_weights(session, paddock_id, start_date, end_date):
    resp = _get(
        session,
        f"{PPL_BASE}/data/cleansed/{paddock_id}/{start_date}/{end_date}",
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_growth(session, paddock_id, start_date, end_date):
    resp = _get(
        session,
        f"{PPL_BASE}/data/reported/{paddock_id}/{start_date}/{end_date}",
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()
