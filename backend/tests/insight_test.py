import json
import urllib.request

BASE = "http://127.0.0.1:8000/api"


def get(url, headers=None):
    r = urllib.request.Request(BASE + url, headers=headers or {})
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())


def post(url, data, headers=None):
    r = urllib.request.Request(
        BASE + url, data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read())


lr = urllib.request.Request(
    BASE + "/auth/login", data=b"username=demo@insightiq.dev&password=demo123",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
token = json.loads(urllib.request.urlopen(lr).read())["access_token"]
h = {"Authorization": f"Bearer {token}"}
ds = get("/datasets", h)["items"][0]
ins = post(f"/insights/generate?dataset_id={ds['id']}", {}, h)["insights"]
print("insight count:", len(ins))
for i in ins:
    print(f"  [{i['category']}/{i['severity']}] {i['title']}")
