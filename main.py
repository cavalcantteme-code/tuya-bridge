import os
from flask import Flask, jsonify, request
from tuya_connector import TuyaOpenAPI

app = Flask(__name__)

ACCESS_ID     = os.environ["TUYA_ACCESS_ID"]
ACCESS_SECRET = os.environ["TUYA_ACCESS_SECRET"]
DEVICE_ID     = os.environ["TUYA_DEVICE_ID"]
ENDPOINT      = os.environ.get("TUYA_ENDPOINT", "https://openapi.tuyaus.com")
WEBHOOK_TOKEN = os.environ["WEBHOOK_TOKEN"]

def get_api():
    openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_SECRET)
    openapi.connect()
    return openapi

@app.route("/plug/<action>", methods=["POST"])
def plug_control(action):
    if request.headers.get("X-Token") != WEBHOOK_TOKEN:
        return jsonify({"error": "unauthorized"}), 401
    if action not in ("on", "off"):
        return jsonify({"error": "use /on ou /off"}), 400
    try:
        openapi = get_api()
        commands = {"commands": [{"code": "switch_1", "value": action == "on"}]}
        result = openapi.post(f"/v1.0/devices/{DEVICE_ID}/commands", commands)
        print("TUYA RESPONSE:", result)
        return jsonify({"action": action, "ok": result.get("success")})
    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
