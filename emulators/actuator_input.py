"""
INPUT ACTUATOR EMULATOR — Manual Feed Button + Mode Switch
Simulates a physical button panel next to the pet feeder.
Operator types commands in the terminal to send MQTT control messages.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paho.mqtt.client as mqtt
import json, time
from config.settings import BROKER_HOST, BROKER_PORT, TOPICS


def run():
    client = mqtt.Client(client_id="pawlytics-actuator-input")
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()

    print("[Input Actuator] Ready.")
    print("  Commands:")
    print("    feed          → trigger a manual feed")
    print("    auto / manual → switch operating mode")
    print("    quit          → exit")

    try:
        while True:
            cmd = input("> ").strip().lower()

            if cmd == "feed":
                payload = json.dumps({"action": "feed", "timestamp": time.time()})
                client.publish(TOPICS["feed_button"], payload)
                print("[Input Actuator] Feed command sent.")

            elif cmd in ("auto", "manual"):
                payload = json.dumps({"mode": cmd, "timestamp": time.time()})
                client.publish(TOPICS["mode"], payload)
                print(f"[Input Actuator] Mode → {cmd}")

            elif cmd == "quit":
                break

            else:
                print("  Unknown command. Try: feed / auto / manual / quit")

    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        print("[Input Actuator] Stopped.")


if __name__ == "__main__":
    run()
