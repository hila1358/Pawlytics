"""
DATA PRODUCER EMULATOR #1 — Food Level Sensor
Simulates a capacitive sensor in the pet food bowl.
Level gradually drops as the pet eats; refilling is triggered by the feeder relay.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt
import json, time, random
from config.settings import BROKER_HOST, BROKER_PORT, TOPICS, SENSOR_INTERVAL


def on_feeder(client, userdata, msg):
    """Refill the bowl when the feeder relay turns on."""
    try:
        payload = json.loads(msg.payload.decode())
        if payload.get("state") == "on":
            userdata["food_level"] = min(100.0, userdata["food_level"] + 40.0)
            print(f"[Food Sensor] Bowl refilled → {userdata['food_level']:.1f}%")
    except Exception:
        pass


def run():
    state = {"food_level": 80.0}

    client = mqtt.Client(client_id="pawlytics-sensor-food", userdata=state)
    client.on_message = on_feeder
    client.connect(BROKER_HOST, BROKER_PORT)
    client.subscribe(TOPICS["feeder"])
    client.loop_start()

    print(f"[Food Sensor] Started → publishing to {TOPICS['food']}")
    try:
        while True:
            # Simulate gradual consumption by the pet
            state["food_level"] -= random.uniform(0.5, 2.0)
            state["food_level"] = max(0.0, state["food_level"])

            payload = json.dumps({
                "value": round(state["food_level"], 1),
                "unit": "%",
                "timestamp": time.time()
            })
            client.publish(TOPICS["food"], payload)
            print(f"[Food Sensor] {state['food_level']:.1f}%")
            time.sleep(SENSOR_INTERVAL)
    except KeyboardInterrupt:
        print("[Food Sensor] Stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
