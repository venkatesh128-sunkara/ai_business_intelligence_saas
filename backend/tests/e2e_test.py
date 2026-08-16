import json
import urllib.request
import urllib.error

FRONT = "http://127.0.0.1:5173"


def get(url):
    try:
        with urllib.request.urlopen(FRONT + url) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# 1. Frontend index served through vite
status, html = get("/")
print("1. frontend / :", status, "has #root:", b'id="root"' in html)

# 2. API proxy through vite -> backend
status, health = get("/api/workspaces")  # auth required -> 401 proves proxy works
print("2. proxy /api/workspaces (no auth):", status, "(expected 401)")

# 3. Full login + ask through the proxy
lr = urllib.request.Request(
    FRONT + "/api/auth/login", data=b"username=demo@insightiq.dev&password=demo123",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
login = json.loads(urllib.request.urlopen(lr).read())
h = {"Authorization": f"Bearer {login['access_token']}"}
req = urllib.request.Request(
    FRONT + "/api/query/ask",
    data=json.dumps({"question": "Show monthly revenue trend", "dataset_id": 1}).encode(),
    headers={"Content-Type": "application/json", **h},
)
res = json.loads(urllib.request.urlopen(req).read())
print("3. ask via proxy :", res["engine"], "| chart", res["chart"]["data"][0]["type"], "| rows", res["row_count"])
