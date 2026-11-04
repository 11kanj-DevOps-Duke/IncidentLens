"""IncidentLens: local demo server, Python standard library only."""
from __future__ import annotations
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from engine import load_examples, load_rules, analyze_incident, from_alertmanager

BASE=Path(__file__).resolve().parent
LATEST={"incident":None, "result":None}
MAX_BODY=64*1024

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.address_string(),fmt % args))
    def send_json(self, status, obj):
        raw=json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        route=urlparse(self.path).path
        if route=="/":
            p=BASE/"static"/"index.html"; data=p.read_bytes()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(data))); self.send_header("X-Content-Type-Options","nosniff"); self.end_headers(); self.wfile.write(data)
        elif route=="/api/examples":
            self.send_json(200,{"examples":load_examples(), "rules_count":len(load_rules()), "ai_available":bool(os.getenv("OPENAI_API_KEY"))})
        elif route=="/api/latest":
            self.send_json(200,{"incident":LATEST["incident"],"result":LATEST["result"]})
        elif route=="/api/health":
            self.send_json(200,{"ok":True,"ai_available":bool(os.getenv("OPENAI_API_KEY")),"read_only":True})
        else: self.send_json(404,{"error":"Route not found"})
    def read_json(self):
        try: size=int(self.headers.get("Content-Length",0))
        except ValueError: raise ValueError("Invalid content length")
        if size<=0 or size>MAX_BODY: raise ValueError("JSON payload must be 1..65536 bytes")
        return json.loads(self.rfile.read(size))
    def do_POST(self):
        route=urlparse(self.path).path
        if route not in ("/api/analyze","/api/webhook/alertmanager","/api/approve"):
            return self.send_json(404,{"error":"Route not found"})
        try:
            payload=self.read_json()
            if not isinstance(payload,dict): raise ValueError("JSON object expected")
            if route=="/api/approve":
                if not LATEST["result"]: raise ValueError("No incident to acknowledge")
                LATEST["result"]["audit"].append("Human acknowledged proposed plan — no commands executed")
                return self.send_json(200,{"ok":True,"audit":LATEST["result"]["audit"]})
            if route=="/api/analyze":
                example_id=payload.get("example_id")
                if example_id:
                    inc=next((x for x in load_examples() if x["id"]==example_id),None)
                    if inc is None: raise ValueError("Example not found")
                elif "alerts" in payload:
                    inc=from_alertmanager(payload)
                else: raise ValueError("Pass example_id or an Alertmanager alerts array")
            else: inc=from_alertmanager(payload)
            use_ai=bool(payload.get("use_ai",True))
            result=analyze_incident(inc, enable_ai=use_ai)
            LATEST["incident"]=inc; LATEST["result"]=result
            self.send_json(200,{"result":result})
        except (ValueError, TypeError, json.JSONDecodeError) as e: self.send_json(400,{"error":str(e)[:250]})
        except Exception as e: self.send_json(500,{"error":type(e).__name__})

if __name__=="__main__":
    port=int(os.environ.get("PORT","8787"))
    server=ThreadingHTTPServer(("127.0.0.1",port),Handler)
    print(f"IncidentLens is running at http://127.0.0.1:{port}\nAI mode: {'ON' if os.getenv('OPENAI_API_KEY') else 'OFF (rules-only demonstration)'}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
