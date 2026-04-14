"""
DATA MANAGER
- Subscribes to all sensor and input topics
- Writes every reading to SQLite (db/pawlytics.db)
- Checks thresholds and publishes warning/alarm messages
- Triggers the feeder relay automatically when food/water is critically low (auto mode)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt
import json, time, sqlite3, threading
from config.settings import (
    BROKER_HOST, BROKER_PORT, TOPICS,
    FOOD_LOW_THRESHOLD, FOOD_CRITICAL_THRESHOLD,
    WATER_LOW_THRESHOLD, WATER_CRITICAL_THRESHOLD,
    ACTIVITY_LOW_THRESHOLD,
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db", "pawlytics.db")


# ── Database helpers ──────────────────────────────────────────────────────────

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor      TEXT    NOT NULL,
            value       REAL    NOT NULL,
            unit        TEXT,
            timestamp   REAL    NOT NULL,
            recorded_at TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            level       TEXT NOT NULL,
            message     TEXT NOT NULL,
            sensor      TEXT,
            value       REAL,
            recorded_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type  TEXT NOT NULL,
            details     TEXT,
            recorded_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conn.commit()
    conn.close()
    print(f"[Manager] Database ready → {DB_PATH}")


def db_exec(sql, params=()):
    """Execute a single write against the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(sql, params)
    conn.commit()
    conn.close()


def save_reading(sensor, value, unit, timestamp):
    db_exec("INSERT INTO readings (sensor, value, unit, timestamp) VALUES (?,?,?,?)",
            (sensor, value, unit, timestamp))


def save_alert(level, message, sensor=None, value=None):
    db_exec("INSERT INTO alerts (level, message, sensor, value) VALUES (?,?,?,?)",
            (level, message, sensor, value))


def save_event(event_type, details=""):
    db_exec("INSERT INTO events (event_type, details) VALUES (?,?)", (event_type, details))


# ── Manager class ─────────────────────────────────────────────────────────────

class PawlyticsManager:
    def __init__(self):
        self.client = mqtt.Client(client_id="pawlytics-manager")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.mode = "auto"

        # Cooldown: only re-send the same alert after this many seconds
        self.alert_cooldown = 30
        self.last_alert_time = {}

    def on_connect(self, client, userdata, flags, rc):
        print(f"[Manager] Connected to broker (rc={rc})")
        for key in ("food", "activity", "water", "feed_button", "mode"):
            client.subscribe(TOPICS[key])
            print(f"[Manager]   subscribed → {TOPICS[key]}")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            return

        topic = msg.topic
        handlers = {
            TOPICS["food"]:        self.handle_food,
            TOPICS["activity"]:    self.handle_activity,
            TOPICS["water"]:       self.handle_water,
            TOPICS["feed_button"]: self.handle_feed_button,
            TOPICS["mode"]:        self.handle_mode,
        }
        handler = handlers.get(topic)
        if handler:
            handler(payload)

    # ── Sensor handlers ───────────────────────────────────────────────────────

    def handle_food(self, payload):
        value = payload["value"]
        save_reading("food", value, payload.get("unit", "%"), payload["timestamp"])
        print(f"[Manager] Food  = {value}%")

        if value <= FOOD_CRITICAL_THRESHOLD:
            self.send_alert("alarm", f"CRITICAL: food level very low ({value}%)", "food", value)
            if self.mode == "auto":
                self._trigger_feeder("Auto-refill: food critically low")
        elif value <= FOOD_LOW_THRESHOLD:
            self.send_alert("warning", f"Food level low ({value}%) — refill soon", "food", value)

    def handle_activity(self, payload):
        value = payload["value"]
        save_reading("activity", value, payload.get("unit", "movements"), payload["timestamp"])
        print(f"[Manager] Activity = {value} movements")

        if value < ACTIVITY_LOW_THRESHOLD:
            self.send_alert("warning", f"Pet appears inactive (activity: {value}). Check on your pet.", "activity", value)

    def handle_water(self, payload):
        value = payload["value"]
        save_reading("water", value, payload.get("unit", "%"), payload["timestamp"])
        print(f"[Manager] Water = {value}%")

        if value <= WATER_CRITICAL_THRESHOLD:
            self.send_alert("alarm", f"CRITICAL: water level very low ({value}%)", "water", value)
        elif value <= WATER_LOW_THRESHOLD:
            self.send_alert("warning", f"Water level low ({value}%) — refill soon", "water", value)

    def handle_feed_button(self, payload):
        print("[Manager] Manual feed button pressed!")
        save_event("manual_feed", "Triggered by operator")
        self._trigger_feeder("Manual feed requested")

    def handle_mode(self, payload):
        self.mode = payload.get("mode", "auto")
        print(f"[Manager] Mode changed → {self.mode}")
        save_event("mode_change", f"Mode set to {self.mode}")

    # ── Actuator commands ─────────────────────────────────────────────────────

    def _trigger_feeder(self, reason=""):
        """Publish feeder ON, then schedule feeder OFF after 3 s (non-blocking)."""
        on_payload = json.dumps({"state": "on", "reason": reason, "timestamp": time.time()})
        self.client.publish(TOPICS["feeder"], on_payload)
        save_event("feeder_triggered", reason)
        print(f"[Manager] Feeder ON → {reason}")

        def turn_off():
            time.sleep(3)
            off_payload = json.dumps({"state": "off", "timestamp": time.time()})
            self.client.publish(TOPICS["feeder"], off_payload)
            print("[Manager] Feeder OFF")

        threading.Thread(target=turn_off, daemon=True).start()

    def send_alert(self, level, message, sensor=None, value=None):
        """Publish an alert with per-sensor cooldown to avoid flooding."""
        key = f"{sensor}_{level}"
        now = time.time()
        if now - self.last_alert_time.get(key, 0) < self.alert_cooldown:
            return
        self.last_alert_time[key] = now

        alert_payload = json.dumps({
            "level": level, "message": message,
            "sensor": sensor, "value": value, "timestamp": now,
        })
        self.client.publish(TOPICS["alerts"], alert_payload)

        buzzer_payload = json.dumps({
            "state": "on", "level": level, "message": message, "timestamp": now,
        })
        self.client.publish(TOPICS["alert"], buzzer_payload)

        save_alert(level, message, sensor, value)
        print(f"[Manager] ALERT [{level.upper()}] {message}")

    # ── Entry point ───────────────────────────────────────────────────────────

    def run(self):
        self.client.connect(BROKER_HOST, BROKER_PORT)
        print("[Manager] Running. Waiting for sensor data...")
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("[Manager] Stopped.")
        finally:
            self.client.disconnect()


if __name__ == "__main__":
    init_db()
    manager = PawlyticsManager()
    manager.run()
