import json
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def post(url, data, headers=None):
    req = urllib.request.Request(
        BASE + url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def get(url, headers=None):
    req = urllib.request.Request(BASE + url, headers=headers or {})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


login_req = urllib.request.Request(
    BASE + "/auth/login",
    data=b"username=demo@insightiq.dev&password=demo123",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
token = json.loads(urllib.request.urlopen(login_req).read())["access_token"]
h = {"Authorization": f"Bearer {token}"}

ds = get("/datasets", h)["items"][0]
ds_id = ds["id"]
print(f"Dataset: {ds['name']} ({ds['row_count']} rows)")

questions = [
    "What were the highest-revenue products?",
    "Total sales by region",
    "Show monthly revenue trend",
    "Average order value by category",
    "How many orders in Q2 2023?",
    "What is the total revenue in North America?",
    "Top 5 customers by total revenue",
    "Show me the data",
    "Total revenue by channel for 2024",
]

for q in questions:
    try:
        res = post("/query/ask", {"question": q, "dataset_id": ds_id}, h)
        ctype = res["chart"]["data"][0]["type"]
        print(f"\nQ: {q}")
        print(f"  SQL: {res['sql']}")
        print(f"  chart={ctype} rows={res['row_count']} engine={res['engine']}")
        if res["rows"]:
            print(f"  first={res['rows'][0]}")
    except Exception as exc:
        print(f"\nQ: {q}\n  ERROR: {exc}")
