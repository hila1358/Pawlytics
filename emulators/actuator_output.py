"""
OUTPUT ACTUATOR EMULATOR — Feeder Relay + Alert Buzzer
Simulates the physical hardware that receives commands from the data manager:
  - Feeder relay: opens the food dispenser when activated
  - Alert buzzer / LED: signals warning or alarm conditions
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt
import json
from config.settings import BROKER_HOST, BROKER_PORT, TOPICS


def on_connect(client, userdata, flags, rc):
    print(f"[Output Actuator] Connected (rc={rc})")
    client.subscribe(TOPICS["feeder"])
    client.subscribe(TOPICS["alert"])
    client.subscribe(TOPICS["alerts"])
    print("[Output Actuator] Subscribed. Waiting for commands...")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    topic = msg.topic

    if topic == TOPICS["feeder"]:
        state = payload.get("state", "off")
        reason = payload.get("reason", "")
        if state == "on":
            print(f"[Feeder Relay]  >>> DISPENSING FOOD <<< ({reason})")
        else:
            print("[Feeder Relay]  Relay OFF — dispensing complete.")

    elif topic == TOPICS["alert"]:
        state = payload.get("state", "off")
        level = payload.get("level", "info")
        message = payload.get("message", "")
        if state == "on":
            prefix = {"warning": "[!!] WARNING", "alarm": "[!!!] ALARM", "info": "[i] INFO"}.get(level, "[?]")
            print(f"[Alert Buzzer]  {prefix}: {message}")
        else:
            print("[Alert Buzzer]  Silenced.")

    elif topic == TOPICS["alerts"]:
        level = payload.get("level", "info")
        message = payload.get("message", "")
        print(f"[Output Actuator] Alert received — {level.upper()}: {message}")


def run():
    client = mqtt.Client(client_id="pawlytics-actuator-output")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT)

    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("[Output Actuator] Stopped.")


if __name__ == "__main__":
    run()
