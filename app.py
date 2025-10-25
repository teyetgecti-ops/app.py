from flask import Flask, request, jsonify
import subprocess
import requests

app = Flask(__name__)

# ---------- SABİT WEBHOOK ----------
WEBHOOK_URL = "https://discord.com/api/webhooks/1430676212489130216/lhHkzELmG00B8EcRJS8o7tPFLuNZ8Q0dHQygjCJ0xn8mzeIZtXCbG2EDQJD6FcorSBlN"

# ---------- ANAHTAR KELİMELER ----------
KEYWORDS = ["disconnected", "respawn"]
REPORTED_LOGS = set()

# ---------- YARDIMCI FONKSİYONLAR ----------
def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=5)
        return out.decode(errors="ignore")
    except Exception:
        return ""

def scan_logcat_for_keywords():
    out = run_cmd("logcat -d -v time | tail -n 200")  # sadece son 200 satır
    found = []
    if not out:
        return found
    lower = out.lower()
    for kw in KEYWORDS:
        idx = 0
        while True:
            idx = lower.find(kw, idx)
            if idx == -1:
                break
            start = lower.rfind("\n", 0, idx) + 1
            end = lower.find("\n", idx)
            if end == -1:
                end = len(lower)
            line = out[start:end].strip()
            if line and line not in REPORTED_LOGS:
                REPORTED_LOGS.add(line)
                found.append(line)
            idx = end
    return found

def post_to_discord(message):
    try:
        requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
    except Exception as e:
        print("Discord gönderilemedi:", e)

# ---------- API ROUTE ----------
@app.route("/scan", methods=["POST"])
def scan():
    data = request.json
    ug_name = data.get("ugname", "UGUnknown")
    interval = data.get("interval", 30)  # opsiyonel, burada sadece logging için

    new_logs = scan_logcat_for_keywords()
    messages = []
    for l in new_logs:
        kw_found = [kw.capitalize() for kw in KEYWORDS if kw in l.lower()]
        if kw_found:
            msg = f"{ug_name}: {', '.join(kw_found)}"
            post_to_discord(msg)
            messages.append(msg)
    return jsonify({"status": "ok", "messages": messages})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
