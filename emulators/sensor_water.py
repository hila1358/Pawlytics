"""
DATA PRODUCER EMULATOR #3 — Water Level Sensor
Simulates a float/ultrasonic sensor in the pet water bowl.
Level drops over time as the pet drinks.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt
import json, time, random
from config.settings import BROKER_HOST, BROKER_PORT, TOPICS, SENSOR_INTERVAL


def run():
    client = mqtt.Client(client_id="pawlytics-sensor-water")
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()

    water_level = 90.0

    print(f"[Water Sensor] Started → publishing to {TOPICS['water']}")
    try:
        while True:
            water_level -= random.uniform(0.3, 1.5)
            water_level = max(0.0, water_level)

            payload = json.dumps({
                "value": round(water_level, 1),
                "unit": "%",
                "timestamp": time.time()
            })
            client.publish(TOPICS["water"], payload)
            print(f"[Water Sensor] {water_level:.1f}%")
            time.sleep(SENSOR_INTERVAL)
    except KeyboardInterrupt:
        print("[Water Sensor] Stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
