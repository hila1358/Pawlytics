# Central configuration for Pawlytics
# Change BROKER_HOST to "broker.hivemq.com" to use a public broker without installing Mosquitto

# Public HiveMQ broker — works without installing Mosquitto locally.
# For a private local setup, change to "localhost" and run Mosquitto.
BROKER_HOST = "broker.hivemq.com"
BROKER_PORT = 1883

# MQTT topic map — all components import from here so topic names stay consistent
TOPICS = {
    "food":        "pawlytics/sensors/food",
    "activity":    "pawlytics/sensors/activity",
    "water":       "pawlytics/sensors/water",
    "feed_button": "pawlytics/actuators/input/feed_button",
    "mode":        "pawlytics/actuators/input/mode",
    "feeder":      "pawlytics/actuators/output/feeder",
    "alert":       "pawlytics/actuators/output/alert",
    "alerts":      "pawlytics/alerts",
}

# Sensor publish interval in seconds
SENSOR_INTERVAL = 3

# Thresholds used by the data manager
FOOD_LOW_THRESHOLD      = 20   # % — Warning below this
FOOD_CRITICAL_THRESHOLD = 10   # % — Alarm below this
WATER_LOW_THRESHOLD     = 20
WATER_CRITICAL_THRESHOLD = 10
ACTIVITY_LOW_THRESHOLD  = 5    # movements per interval — Warning when pet is inactive
