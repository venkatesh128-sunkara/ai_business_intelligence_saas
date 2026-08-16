import json
import io
import urllib.request
import urllib.error
import uuid

BASE = "http://127.0.0.1:8000/api"


def req(method, url, data=None, headers=None, content_type=None):
    body = None
    hdr = dict(headers or {})
    if data is not None and not isinstance(data, bytes):
        body = json.dumps(data).encode()
        hdr["Content-Type"] = "application/json"
    elif isinstance(data, bytes):
        body = data
        if content_type:
            hdr["Content-Type"] = content_type
    r = urllib.request.Request(BASE + url, data=body, headers=hdr, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:800]


status, login = req("POST", "/auth/login", headers={"Content-Type": "application/x-www-form-urlencoded"})
# do form login properly
lr = urllib.request.Request(
    BASE + "/auth/login", data=b"username=demo@insightiq.dev&password=demo123",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
token = json.loads(urllib.request.urlopen(lr).read())["access_token"]
h = {"Authorization": f"Bearer {token}"}

status, ds = req("GET", "/datasets", headers=h)
ds_id = ds["items"][0]["id"]
print("1. datasets:", status, "total", ds["total"])

status, ins = req("POST", f"/insights/generate?dataset_id={ds_id}", {}, headers=h)
print("2. insights:", status, "count", len(ins["insights"]))
for i in ins["insights"][:3]:
    print("   -", i["title"], f"[{i['severity']}]")

# create a query record to add to dashboard
status, q = req("POST", "/query/ask", {"question": "Revenue by region", "dataset_id": ds_id}, h)
qid = q["id"]
print("3. ask:", status, "qid", qid)

ws_id = ds["items"][0]["workspace_id"]
status, dash = req("POST", f"/dashboards?workspace_id={ws_id}", {"name": "My Dashboard"}, h)
dash_id = dash["id"]
status, item = req("POST", f"/dashboards/{dash_id}/items", {"query_id": qid, "title": "Revenue by region"}, h)
print("4. dashboard:", status, "id", dash_id, "item id", item["id"])

status, items = req("GET", f"/dashboards/{dash_id}", headers=h)
print("5. dashboard get:", status, "items", len(items["items"]))

# upload a new CSV
csv_data = "date,product,revenue,region\n2024-01-01,Widget,100,US\n2024-01-02,Gadget,250,EU\n2024-01-03,Widget,150,US\n".encode()
boundary = uuid.uuid4().hex
parts = [
    f'--{boundary}\r\nContent-Disposition: form-data; name="workspace_id"\r\n\r\n{ws_id}\r\n'.encode(),
    f'--{boundary}\r\nContent-Disposition: form-data; name="name"\r\n\r\nMy Upload\r\n'.encode(),
    f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="upload.csv"\r\nContent-Type: text/csv\r\n\r\n'.encode(),
    csv_data,
    f'\r\n--{boundary}--\r\n'.encode(),
]
body = b"".join(parts)
status, up = req("POST", "/datasets", body, h, f"multipart/form-data; boundary={boundary}")
print("6. upload:", status, "name", up.get("name"), "rows", up.get("row_count"))

status, hist = req("GET", "/query/history", {}, headers=h)
print("7. history:", status, "total", hist["total"])

# admin
lr2 = urllib.request.Request(
    BASE + "/auth/login", data=b"username=admin@insightiq.dev&password=admin123",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
adm = json.loads(urllib.request.urlopen(lr2).read())["access_token"]
ha = {"Authorization": f"Bearer {adm}"}
status, stats = req("GET", "/admin/stats", {}, headers=ha)
print("8. admin stats:", status, {k: stats[k] for k in ("users", "workspaces", "datasets", "queries", "dashboards")})

status, usage = req("GET", f"/workspaces/{ws_id}/usage", {}, headers=h)
print("9. usage:", status, "queries", usage["query_count"], "/", usage["query_limit"])

