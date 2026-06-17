"""
Khoj demo server.

A zero-dependency web demo so a recruiter (or a judge) can paste a job
description and watch the ranking happen live, with hidden-gem badges, score
breakdowns, and the evidence behind every call.

Run:
    python demo/server.py
then open http://localhost:8000

Pure standard library. No build step, no framework, works offline.
"""

import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from khoj import data_io, jd          # noqa: E402
from khoj.rank import Ranker          # noqa: E402

RAW = ROOT / "data" / "raw"
HERE = Path(__file__).resolve().parent

print("Loading candidates and building the index...")
CANDIDATES, STATS = data_io.load_profiles(RAW / "profiles.jsonl")
JOBS = {j["job_id"]: j for j in data_io.load_jobs(RAW / "jobs.json")}
RANKER = Ranker(retrieve_n=60).fit(CANDIDATES)
print(f"Ready. {len(CANDIDATES)} candidates indexed. Open http://localhost:8000")


def rank_payload(job_dict, top_k=10):
    spec = jd.parse(job_dict)
    t0 = time.perf_counter()
    ranked = RANKER.rank(spec, top_k=top_k)
    ms = (time.perf_counter() - t0) * 1000
    return {
        "job_title": job_dict.get("title", "Custom role"),
        "pedigree_agnostic": spec["pedigree_agnostic"],
        "must_have": spec["must_have"],
        "nice_to_have": spec["nice_to_have"],
        "latency_ms": round(ms, 2),
        "pool_size": len(CANDIDATES),
        "shortlist": ranked,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/api/jobs":
            self._send(200, json.dumps([
                {"job_id": j["job_id"], "title": j["title"], "description": j["description"]}
                for j in JOBS.values()
            ]))
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if self.path != "/api/rank":
            self._send(404, json.dumps({"error": "not found"}))
            return
        length = int(self.headers.get("Content-Length", 0))
        req = json.loads(self.rfile.read(length) or b"{}")
        if req.get("job_id") in JOBS:
            job = JOBS[req["job_id"]]
        else:
            job = {
                "title": req.get("title", "Custom role"),
                "description": req.get("description", ""),
                "must_have": req.get("must_have", []),
                "nice_to_have": req.get("nice_to_have", []),
                "min_experience_years": req.get("min_experience_years", 0),
                "seniority": req.get("seniority", "mid"),
            }
        self._send(200, json.dumps(rank_payload(job, top_k=int(req.get("top_k", 10)))))


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
