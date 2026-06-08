import hashlib
import hmac
import json
import os
import time

import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

ACCESS_ID     = os.environ["TUYA_ACCESS_ID"]
ACCESS_SECRET = os.environ["TUYA_ACCESS_SECRET"]
DEVICE_ID     = os.environ["TUYA_DEVICE_ID"]
ENDPOINT      = os.environ.get("TUYA_ENDPOINT", "https://openapi.tuyaus.com")
WEBHOOK_TOKEN = os.environ["WEBHOOK_TOKEN"]

def _sign(secret, msg):
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest().upper()

def get_token():
    t = str(int(time.time() * 1000))
    path = "/v1.0/token?grant_type=1"
    sign = _sign(ACCESS_SECRET, f"{ACCESS_ID}{t}GET\n\n\n\n{path}")
    headers = {"client_id": ACCESS_ID, "sign": sign,
               "t": t, "sign_method": "HMAC-SHA256"}
    r = requests.get(f"{ENDPOINT}{path}", headers=headers, timeout=8)
    data = r.json()
    print("TUYA TOKEN RESPONSE:", data)
    if not data.get("success"):
        raise RuntimeError(f"Token error: {data}")
    return data["result"]["access_token"]

def control_device(token, state):
    t = str(int(time.time() * 1000))
    path = f"/v1.0/devices/{DEVICE_ID}/commands"
    body = json.dumps({"commands": [{"code": "switch_1", "value": state}]})
    h = hashlib.sha256(body.encode()).hexdigest()
    sign = _sign(ACCESS_SECRET,
        f"{ACCESS_ID}{token}{t}POST\n{h}\napplication/json\n\n{path}")
    headers = {"client_id": ACCESS_ID, "access_token": token,
               "sign": sign, "t": t, "sign_method": "HMAC-SHA256",
               "Content-Type": "application/json"}
    return requests.post(f"{ENDPOINT}{path}",
                         headers=headers, data=body, timeout=8).json()

@app.route("/plug/<action>", methods=["POST"])
def plug_control(action):
    if request.headers.get("X-Token") != WEBHOOK_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    if action not in ("on", "off"):
        return jsonify({"error": "use /on ou /off"}), 400
    try:
        token = get_token()
        result = control_device(token, action == "on")
        return jsonify({"action": action, "ok": result.get("success")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
