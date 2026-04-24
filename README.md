# Pawlytics — Smart Pet Monitoring System

An IoT project built with Python and MQTT that monitors a pet's food level, water level,
and daily activity in real time, automatically triggers the feeder when supplies run low,
and alerts the owner through a live dashboard.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         MQTT Broker                              │
│                  (Mosquitto / HiveMQ public)                     │
└────┬──────────────┬──────────────┬─────────────┬────────────────┘
     │              │              │             │
     ▼              ▼              ▼             ▼
 sensor_food   sensor_water  sensor_activity  actuator_input
 (publishes)   (publishes)   (publishes)      (publishes feed/mode)
                                                        │
                                             ┌──────────▼──────────┐
                                             │   data_manager /    │
                                             │   manager.py        │
                                             │  - reads DB         │
                                             │  - checks thresholds│
                                             │  - sends alerts     │
                                             └──┬──────────┬───────┘
                                                │          │
                                     ┌──────────▼──┐  ┌───▼──────────────┐
                                     │  SQLite DB  │  │  actuator_output │
                                     │ pawlytics.db│  │  (feeder relay + │
                                     └─────────────┘  │   alert buzzer)  │
                                                       └──────────────────┘
                                                                │
                                                       ┌────────▼─────────┐
                                                       │   gui/dashboard  │
                                                       │  (live display + │
                                                       │   alert log)     │
                                                       └──────────────────┘
```

---

## Project Structure

```
Pawlytics/
├── config/
│   └── settings.py           # Broker address, topic names, thresholds
├── emulators/
│   ├── sensor_food.py        # Data producer: food level (%)
│   ├── sensor_activity.py    # Data producer: pet activity (movements)
│   ├── sensor_water.py       # Data producer: water level (%)
│   ├── actuator_input.py     # Input actuator: manual feed button + mode switch
│   └── actuator_output.py    # Output actuator: feeder relay + alert buzzer
├── data_manager/
│   └── manager.py            # Subscribes to topics, writes DB, sends alerts
├── gui/
│   ├── dashboard.py          # Flask server — serves the web dashboard at http://localhost:5000
│   └── templates/
│       └── index.html        # Mobile-style single-page app (MQTT.js + Chart.js)
├── db/                       # Auto-created at runtime
│   └── pawlytics.db          # SQLite database
├── requirements.txt
└── README.md
```

---

## MQTT Topics

| Purpose                  | Topic                                  | Publisher             | Subscribers                  |
|--------------------------|----------------------------------------|-----------------------|------------------------------|
| Food level reading       | `pawlytics/sensors/food`               | sensor_food           | manager, dashboard           |
| Activity reading         | `pawlytics/sensors/activity`           | sensor_activity       | manager, dashboard           |
| Water level reading      | `pawlytics/sensors/water`              | sensor_water          | manager, dashboard           |
| Manual feed trigger      | `pawlytics/actuators/input/feed_button`| actuator_input / GUI  | manager                      |
| Mode switch              | `pawlytics/actuators/input/mode`       | actuator_input / GUI  | manager, dashboard           |
| Feeder relay command     | `pawlytics/actuators/output/feeder`    | manager               | actuator_output, sensor_food, dashboard |
| Alert buzzer command     | `pawlytics/actuators/output/alert`     | manager               | actuator_output, dashboard   |
| Warning / alarm messages | `pawlytics/alerts`                     | manager               | actuator_output, dashboard   |

---

## Thresholds (configured in `config/settings.py`)

| Sensor   | Warning     | Alarm (Critical) |
|----------|-------------|------------------|
| Food     | < 20 %      | < 10 %           |
| Water    | < 20 %      | < 10 %           |
| Activity | < 5 moves   | —                |

When food drops below the alarm threshold and the system is in **auto mode**, the feeder relay
is triggered automatically.

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

> `sqlite3` is part of the Python standard library — no extra install needed.

### 2. Start an MQTT broker

**Option A — Local Mosquitto (recommended):**
```bash
mosquitto
```

**Option B — Public broker (no install):**
Edit `config/settings.py` and set:
```python
BROKER_HOST = "broker.hivemq.com"
```

### 3. Open separate terminals and start each component

```bash
# Terminal 1 — Data Manager (start first so it initialises the DB)
python data_manager/manager.py

# Terminal 2 — GUI Dashboard
python gui/dashboard.py

# Terminal 3 — Food sensor
python emulators/sensor_food.py

# Terminal 4 — Water sensor
python emulators/sensor_water.py

# Terminal 5 — Activity sensor
python emulators/sensor_activity.py

# Terminal 6 — Output actuator (feeder relay + buzzer)
python emulators/actuator_output.py

# Terminal 7 — Input actuator (optional — you can also use the Feed button in the GUI)
python emulators/actuator_input.py
```

### 4. Demo flow (5–7 minutes)

1. Start manager + GUI — show the empty dashboard.
2. Start all three sensors — watch values update live.
3. Wait for food or water to drop below 20 % — observe **[WARN]** in the alarm log.
4. Wait for the critical threshold (10 %) — observe **[ALARM]** and the feeder relay firing.
5. Press **FEED NOW** in the GUI — show manual override.
6. Switch to **Manual Mode** — show that the auto-refill no longer fires automatically.
7. Start `actuator_input.py` — type `feed` to trigger a feed from the terminal.

---

## Database

SQLite file is created automatically at `db/pawlytics.db` when the manager starts.

| Table      | Columns                                             | Purpose                     |
|------------|-----------------------------------------------------|-----------------------------|
| `readings` | sensor, value, unit, timestamp, recorded_at         | Every sensor reading        |
| `alerts`   | level, message, sensor, value, recorded_at          | All warnings and alarms     |
| `events`   | event_type, details, recorded_at                    | Feed triggers, mode changes |

---

## Grading Rubric Mapping

| Requirement              | File(s)                                          | What it does                                              |
|--------------------------|--------------------------------------------------|-----------------------------------------------------------|
| **Data producer emulators** (≥1) | `emulators/sensor_food.py` <br> `emulators/sensor_activity.py` <br> `emulators/sensor_water.py` | Publish food %, activity count, water % to MQTT |
| **Input actuator emulator** (≥1) | `emulators/actuator_input.py`               | Terminal button: triggers manual feed, switches mode       |
| **Output actuator emulator** (≥1)| `emulators/actuator_output.py`              | Simulates feeder relay opening + alert buzzer/LED firing   |
| **Data manager**         | `data_manager/manager.py`                        | Subscribes to broker, writes SQLite, evaluates thresholds, publishes alerts |
| **DB writes**            | `data_manager/manager.py` + `db/pawlytics.db`    | Every reading, alert, and event persisted in SQLite        |
| **Warning / alarm messages** | `data_manager/manager.py`                   | `send_alert()` publishes to `pawlytics/alerts` with level = warning / alarm |
| **GUI — live data**      | `gui/dashboard.py` + `gui/templates/index.html`  | Values update in real time via MQTT.js WebSocket           |
| **GUI — device states**  | `gui/templates/index.html`                       | Feeder relay state, mode, and connection status shown live |
| **GUI — Info/Warn/Alarm log** | `gui/templates/index.html`                  | Colour-coded alert log with filter buttons (All / Warn / Alarm) |
