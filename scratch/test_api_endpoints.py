import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

print("Step 1: importing FastAPI and app...")

from fastapi.testclient import TestClient
print("Step 2: importing api.main...")
from api.main import app
print("Step 3: creating TestClient...")
client = TestClient(app)
print("Step 4: calling /case/sample...")
resp = client.get("/case/sample")
print("Sample status:", resp.status_code, len(resp.json()))
sample = resp.json()[0]
print("Sample 1 title:", sample["case_title"])

print("Step 5: calling /case/extract-text...")
text_resp = client.post(
    "/case/extract-text",
    json={
        "raw_text": "IN THE COURT OF SESSIONS JUDGE, PUNE\nState vs Ramesh\nFIR No. 10/2023\nu/s 302 IPC",
        "redact_pii": True,
    },
)
print("Extract status:", text_resp.status_code, text_resp.json()["sections"])

print("Step 6: calling /case/analyze...")
analysis_resp = client.post("/case/analyze", json=sample)
print("Analyze status:", analysis_resp.status_code)
data = analysis_resp.json()
print("Glance:", data["glance"]["case_title"])
print("Duration:", data["duration_prediction"]["status_label"], data["duration_prediction"]["expected_duration_months"], "months")
print("Bail:", data["bail_assessment"]["status_label"])
print("Similar:", data["similar_cases"]["match_level"], data["similar_cases"]["total_historical_matches"])
print("Roadmap steps:", len(data["procedural_roadmap"]))
print("ALL TESTS PASSED!")
