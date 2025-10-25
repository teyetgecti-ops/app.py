from flask import Flask, request, jsonify
import subprocess
import time
import requests
import threading

app = Flask(__name__)

# ---------- SABİT WEBHOOK ----------
webhook_url = "https://discord.com/api/webhooks/1430676212489130216/lhHkzELmG00B8EcRJS8o7tPFLuNZ8Q0dHQygjCJ0xn8mzeIZtXCbG2EDQJD6FcorSBlN"

# ---------- ANAHTAR KELİMELER ----------
keywords = ["disconnected", "respawn"]
reported_logs = set()


def run_cmd(cmd):
    try:
        out = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=5)
        return out.decode(errors="ignore")
    except Exception:
        return ""


def scan_logcat_for_keywords():
    out = run_cmd("logcat -d -v time | tail -n 200")  # son 200 satır
    found = []
    if not out:
        return found
    lower = out.lower()
    for kw in keywords:
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
            if line and line not in reported_logs:
                reported_logs.add(line)
                found.append(line)
            idx = end
    return found


def post_to_discord(message):
    try:
        requests.post(webhook_url, json={"content": message}, timeout=10)
    except Exception as e:
        print("Discord gönderilemedi:", e)


def log_loop(ug_name, interval):
    loop_counter = 0
    while True:
        loop_counter += 1
        new_logs = scan_logcat_for_keywords()
        if new_logs:
            for l in new_logs:
                kw_found = [kw.capitalize() for kw in keywords if kw in l.lower()]
                if kw_found:
                    msg = f"{ug_name}: {', '.join(kw_found)}"
                    post_to_discord(msg)
                    print(msg)
        time.sleep(interval)


@app.route("/start", methods=["POST"])
def start_agent():
    data = request.json
    ug_name = data.get("ugname", "UG1")
    interval = data.get("interval", 30)
    thread = threading.Thread(target=log_loop, args=(ug_name, interval))
    thread.daemon = True
    thread.start()
    return jsonify({"status": "agent started", "ugname": ug_name, "interval": interval})


@app.route("/", methods=["GET"])
def index():
    return "UGTakip API is running."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
