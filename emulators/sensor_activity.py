"""
DATA PRODUCER EMULATOR #2 — Pet Activity Sensor
Simulates a motion/accelerometer sensor on the pet's collar.
Alternates between active bursts and resting periods.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt
import json, time, random
from config.settings import BROKER_HOST, BROKER_PORT, TOPICS, SENSOR_INTERVAL


def run():
    client = mqtt.Client(client_id="pawlytics-sensor-activity")
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()

    resting = False
    rest_ticks = 0

    print(f"[Activity Sensor] Started → publishing to {TOPICS['activity']}")
    try:
        while True:
            if resting:
                activity = random.randint(0, 3)
                rest_ticks += 1
                if rest_ticks >= 5:   # rest for ~5 intervals then wake up
                    resting = False
                    rest_ticks = 0
            else:
                activity = random.randint(8, 35)
                if random.random() < 0.2:   # 20% chance to start a rest period
                    resting = True

            payload = json.dumps({
                "value": activity,
                "unit": "movements",
                "timestamp": time.time()
            })
            client.publish(TOPICS["activity"], payload)
            status = "(resting)" if resting else ""
            print(f"[Activity Sensor] {activity} movements {status}")
            time.sleep(SENSOR_INTERVAL)
    except KeyboardInterrupt:
        print("[Activity Sensor] Stopped.")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    run()
