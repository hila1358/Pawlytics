"""
MAIN GUI — Pawlytics Web Dashboard
Serves the dashboard as a webpage on http://localhost:5000
The browser connects directly to the MQTT broker via WebSocket (MQTT.js).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import threading, webbrowser
from flask import Flask, render_template

app = Flask(__name__, template_folder="templates")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    # Open browser automatically after a short delay
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5000")).start()
    print("[Dashboard] Open http://localhost:5000 in your browser")
    app.run(host="0.0.0.0", port=5000, debug=False)
